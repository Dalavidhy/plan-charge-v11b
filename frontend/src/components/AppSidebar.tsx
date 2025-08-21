import { CalendarDays, ClipboardList, Cog, Users, Ticket } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
} from "@/components/ui/sidebar";
import NDALogo from "@/assets/NDA_LOGO_BASELINE_RVB.svg";

export function AppSidebar() {
  const location = useLocation();
  const currentPath = location.pathname;
  const navItems = [
    { title: "Plan de charge", url: "/plan", icon: CalendarDays },
    { title: "Droits TR", url: "/droits-tr", icon: Ticket },
    { title: "Collaborateurs", url: "/collaborateurs", icon: Users },
    { title: "Synchronisation", url: "/sync", icon: Cog },
  ];

  const isActive = (path: string) => currentPath === path;

  return (
    <Sidebar>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.url}>
                  <SidebarMenuButton asChild isActive={isActive(item.url)}>
                    <NavLink to={item.url} end>
                      <item.icon />
                      <span>{item.title}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarSeparator />

        <SidebarGroup>
          <SidebarGroupContent>
            <div className="flex justify-center p-4">
              <img
                src={NDALogo}
                alt="NDA Partners"
                className="h-72 w-auto opacity-100"
              />
            </div>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
