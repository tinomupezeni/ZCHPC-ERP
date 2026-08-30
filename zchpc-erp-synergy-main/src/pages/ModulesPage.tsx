import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { getModules, installModule, uninstallModule, SystemModule } from '@/services/system.services';
import { toast } from 'sonner';
import { Package, Download, Trash2, CheckCircle2 } from 'lucide-react';

const ModulesPage = () => {
  const [modules, setModules] = useState<SystemModule[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchModules();
  }, []);

  const fetchModules = async () => {
    try {
      const data = await getModules();
      setModules(data);
    } catch (error) {
      toast.error('Failed to fetch modules');
    } finally {
      setLoading(false);
    }
  };

  const handleInstall = async (identifier: string) => {
    try {
      await installModule(identifier);
      toast.success('Module installed successfully');
      fetchModules();
      // Reload page to update navigation
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (error) {
      toast.error('Failed to install module');
    }
  };

  const handleUninstall = async (identifier: string) => {
    try {
      await uninstallModule(identifier);
      toast.success('Module uninstalled successfully');
      fetchModules();
      // Reload page to update navigation
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (error) {
      toast.error('Failed to uninstall module');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-full">Loading modules...</div>;
  }

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">App Store</h1>
          <p className="text-slate-500 mt-2">Manage your ERP modules and extensions.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {modules.map((module) => (
          <Card key={module.id} className="flex flex-col">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="p-2 bg-slate-100 rounded-lg">
                  <Package className="h-6 w-6 text-slate-600" />
                </div>
                {module.is_active && (
                  <div className="flex items-center text-green-600 text-xs font-medium">
                    <CheckCircle2 className="h-4 w-4 mr-1" />
                    Installed
                  </div>
                )}
              </div>
              <CardTitle className="mt-4">{module.name}</CardTitle>
              <CardDescription>{module.description}</CardDescription>
            </CardHeader>
            <CardContent className="flex-1">
              <div className="text-xs text-slate-500">
                Identifier: <code className="bg-slate-50 px-1 rounded">{module.identifier}</code>
              </div>
              {module.dependencies.length > 0 && (
                <div className="mt-2">
                  <span className="text-xs font-medium text-slate-700">Dependencies:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {module.dependencies.map((dep) => (
                      <span key={dep} className="text-[10px] bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">
                        {dep}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
            <CardFooter className="border-t pt-4">
              {module.is_active ? (
                <Button 
                  variant="outline" 
                  className="w-full text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                  onClick={() => handleUninstall(module.identifier)}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Uninstall
                </Button>
              ) : (
                <Button 
                  className="w-full bg-blue-600 hover:bg-blue-700"
                  onClick={() => handleInstall(module.identifier)}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Install
                </Button>
              )}
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default ModulesPage;
