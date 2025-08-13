import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { LogOut } from "lucide-react";

export default function AppLayout({ children, title }: { children: React.ReactNode; title?: string }) {
  const { logout, userEmail } = useAuth();

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <SidebarInset>
          <header className="h-14 flex items-center border-b bg-background/70 backdrop-blur-sm">
            <div className="flex items-center gap-3 px-4 w-full">
              <SidebarTrigger />
              <div className="flex-1">
                <h1 className="text-lg font-semibold">{title ?? "Plateforme RH"}</h1>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground hidden sm:inline">{userEmail}</span>
                <Button variant="outline" size="sm" onClick={logout}>
                  <LogOut className="mr-2" /> Déconnexion
                </Button>
              </div>
            </div>
          </header>
          <main className="p-4">
            {children}
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}
