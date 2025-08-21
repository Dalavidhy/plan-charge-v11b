"""
Payfit API Client for interacting with Payfit Partner API
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import httpx
from httpx import AsyncClient, HTTPStatusError

from app.config import settings

logger = logging.getLogger(__name__)


class PayfitAPIClient:
    """Client for Payfit Partner API v1.0"""

    def __init__(self):
        self.base_url = settings.PAYFIT_API_URL
        self.api_key = settings.PAYFIT_API_KEY
        self.company_id = settings.PAYFIT_COMPANY_ID

        # Check if credentials are properly configured
        self.is_configured = (
            self.api_key
            and self.api_key != "placeholder-payfit-key"
            and self.company_id
            and self.company_id != "placeholder-company-id"
        )

        if not self.is_configured:
            logger.warning(
                "Payfit API credentials not properly configured - using mock mode"
            )
            self.api_key = "mock-key"
            self.company_id = "mock-company"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        timeout: int = 30,
    ) -> Dict:
        """Make HTTP request to Payfit API"""
        url = f"{self.base_url}{endpoint}"

        async with AsyncClient(timeout=timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=data,
                )
                response.raise_for_status()
                return response.json()
            except HTTPStatusError as e:
                logger.error(
                    f"Payfit API error: {e.response.status_code} - {e.response.text}"
                )
                raise Exception(
                    f"Payfit API error: {e.response.status_code} - {e.response.text}"
                )
            except Exception as e:
                logger.error(f"Payfit API request failed: {str(e)}")
                raise

    async def test_connection(self) -> bool:
        """Test API connection and authentication"""
        if not self.is_configured:
            logger.info("Payfit API is in mock mode - connection test returns True")
            return True

        try:
            # Try to get company info
            result = await self.get_company()
            return True
        except Exception as e:
            logger.error(f"Payfit connection test failed: {str(e)}")
            return False

    # Company endpoint
    async def get_company(self) -> Dict:
        """Get company information"""
        if not self.is_configured:
            return {
                "id": "mock-company",
                "name": "Mock Company for Development",
                "status": "active",
            }

        endpoint = f"/companies/{self.company_id}"
        return await self._make_request("GET", endpoint)

    # Collaborator (Employee) endpoints
    async def get_collaborators(
        self,
        max_results: int = 10,
        next_page_token: Optional[str] = None,
        include_in_progress_contracts: bool = False,
        email: Optional[str] = None,
    ) -> Dict:
        """Get list of collaborators (employees)"""
        if not self.is_configured:
            return {
                "nextPageToken": None,
                "collaborators": [],  # Return empty list in mock mode
            }

        endpoint = f"/companies/{self.company_id}/collaborators"
        params = {"maxResults": str(min(max_results, 50))}  # Max 50 according to API

        if next_page_token:
            params["nextPageToken"] = next_page_token

        if include_in_progress_contracts:
            params["includeInProgressContracts"] = "true"

        if email:
            params["email"] = email

        return await self._make_request("GET", endpoint, params=params)

    async def get_collaborator(self, collaborator_id: str) -> Dict:
        """Get specific collaborator details"""
        endpoint = f"/companies/{self.company_id}/collaborators/{collaborator_id}"
        return await self._make_request("GET", endpoint)

    async def get_all_collaborators(
        self, include_in_progress_contracts: bool = False
    ) -> List[Dict]:
        """Get all collaborators with pagination handling"""
        all_collaborators = []
        next_page_token = None

        while True:
            result = await self.get_collaborators(
                max_results=50,
                next_page_token=next_page_token,
                include_in_progress_contracts=include_in_progress_contracts,
            )

            collaborators = result.get("collaborators", [])
            all_collaborators.extend(collaborators)

            # Check for next page
            meta = result.get("meta", {})
            next_page_token = meta.get("nextPageToken")
            if not next_page_token:
                break

        logger.info(f"Retrieved {len(all_collaborators)} collaborators from Payfit")
        return all_collaborators

    # For backward compatibility, map employees to collaborators
    async def get_employees(
        self,
        limit: int = 10,
        page_token: Optional[str] = None,
        include_terminated: bool = False,
    ) -> Dict:
        """Get list of employees (wrapper for collaborators)"""
        result = await self.get_collaborators(
            max_results=limit,
            next_page_token=page_token,
            include_in_progress_contracts=include_terminated,
        )

        # Transform response to match expected format
        return {
            "employees": result.get("collaborators", []),
            "nextPageToken": result.get("meta", {}).get("nextPageToken"),
        }

    async def get_all_employees(self, include_terminated: bool = False) -> List[Dict]:
        """Get all employees (wrapper for collaborators)"""
        return await self.get_all_collaborators(include_terminated)

    # Absence endpoints
    async def get_absences(
        self,
        max_results: int = 10,
        next_page_token: Optional[str] = None,
        contract_id: Optional[str] = None,
        status: str = "approved",
        begin_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict:
        """Get list of absences"""
        if not self.is_configured:
            return {
                "nextPageToken": None,
                "absences": [],  # Return empty list in mock mode
            }

        endpoint = f"/companies/{self.company_id}/absences"
        params = {"maxResults": str(min(max_results, 50)), "status": status}

        if next_page_token:
            params["nextPageToken"] = next_page_token

        if contract_id:
            params["contractId"] = contract_id

        if begin_date:
            params["beginDate"] = begin_date.isoformat()

        if end_date:
            params["endDate"] = end_date.isoformat()

        return await self._make_request("GET", endpoint, params=params)

    async def get_all_absences(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: str = "all",
    ) -> List[Dict]:
        """Get all absences with pagination handling"""
        all_absences = []
        next_page_token = None

        while True:
            result = await self.get_absences(
                max_results=50,
                next_page_token=next_page_token,
                status=status,
                begin_date=start_date,
                end_date=end_date,
            )

            absences = result.get("absences", [])
            all_absences.extend(absences)

            # Check for next page
            meta = result.get("meta", {})
            next_page_token = meta.get("nextPageToken")
            if not next_page_token:
                break

        logger.info(f"Retrieved {len(all_absences)} absences from Payfit")
        return all_absences

    # Contract data is included in collaborators
    async def get_all_contracts(self, employee_id: Optional[str] = None) -> List[Dict]:
        """Get all contracts (extracted from collaborators)"""
        collaborators = await self.get_all_collaborators(
            include_in_progress_contracts=True
        )

        all_contracts = []
        for collab in collaborators:
            contracts = collab.get("contracts", [])
            for contract in contracts:
                # Add collaborator ID to contract for reference
                contract["collaboratorId"] = collab["id"]
                if not employee_id or collab["id"] == employee_id:
                    all_contracts.append(contract)

        logger.info(f"Extracted {len(all_contracts)} contracts from collaborators")
        return all_contracts

    # Payslip endpoints
    async def get_payslips(
        self, collaborator_id: str, limit: int = 10, page_token: Optional[str] = None
    ) -> Dict:
        """Get list of payslips for a collaborator"""
        endpoint = (
            f"/companies/{self.company_id}/collaborators/{collaborator_id}/payslips"
        )
        params = {"limit": limit}

        if page_token:
            params["pageToken"] = page_token

        return await self._make_request("GET", endpoint, params=params)

    async def get_payslip(
        self, collaborator_id: str, contract_id: str, payslip_id: str
    ) -> Dict:
        """Get specific payslip details"""
        endpoint = f"/companies/{self.company_id}/collaborators/{collaborator_id}/contracts/{contract_id}/payslips/{payslip_id}"
        return await self._make_request("GET", endpoint)
