import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { documentService } from '@/services/document.service';
import { DocumentsList } from '@/components/documents/DocumentsList';
import type {
  DocumentListItem,
  DocumentCategory,
  DocumentSummary,
} from '@/types/document.types';
import {
  FolderOpen,
  FileText,
  AlertCircle,
  Download,
  CheckCircle,
  ExternalLink,
} from 'lucide-react';
import { format } from 'date-fns';

function SummaryCard({
  title,
  count,
  icon,
  color,
}: {
  title: string;
  count: number;
  icon: React.ReactNode;
  color: string;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold">{count}</p>
          </div>
          <div className={`p-2 rounded-full ${color}`}>{icon}</div>
        </div>
      </CardContent>
    </Card>
  );
}

export function DocumentsPage() {
  const { toast } = useToast();

  // State
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [categories, setCategories] = useState<DocumentCategory[]>([]);
  const [fileTypes, setFileTypes] = useState<string[]>([]);
  const [summary, setSummary] = useState<DocumentSummary | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<DocumentListItem | null>(
    null
  );

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<number | null>(null);
  const [fileTypeFilter, setFileTypeFilter] = useState('');

  // Loading states
  const [isLoading, setIsLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState<number | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  // Fetch documents
  const fetchDocuments = useCallback(async () => {
    try {
      const params: {
        category?: number;
        file_type?: string;
        search?: string;
      } = {};

      if (categoryFilter) params.category = categoryFilter;
      if (fileTypeFilter && fileTypeFilter !== 'all')
        params.file_type = fileTypeFilter;
      if (searchQuery) params.search = searchQuery;

      const data = await documentService.getDocuments(params);
      setDocuments(data);
    } catch (error) {
      console.error('Error fetching documents:', error);
      toast({
        title: 'Error',
        description: 'Failed to load documents',
        variant: 'destructive',
      });
    }
  }, [categoryFilter, fileTypeFilter, searchQuery, toast]);

  // Fetch summary
  const fetchSummary = async () => {
    try {
      const data = await documentService.getSummary();
      setSummary(data);
    } catch (error) {
      console.error('Error fetching summary:', error);
    }
  };

  // Fetch categories and file types
  const fetchOptions = async () => {
    try {
      const [categoriesData, fileTypesData] = await Promise.all([
        documentService.getCategories(),
        documentService.getFileTypes(),
      ]);
      setCategories(categoriesData);
      setFileTypes(fileTypesData);
    } catch (error) {
      console.error('Error fetching options:', error);
    }
  };

  // Initial load
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      await Promise.all([fetchDocuments(), fetchSummary(), fetchOptions()]);
      setIsLoading(false);
    };
    loadData();
  }, []);

  // Reload documents when filters change
  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // Handle download
  const handleDownload = async (document: DocumentListItem) => {
    setDownloadingId(document.id);
    try {
      const blob = await documentService.downloadDocument(document.id);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = window.document.createElement('a');
      link.href = url;
      link.download = `${document.title}.${document.file_type}`;
      window.document.body.appendChild(link);
      link.click();
      window.document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast({
        title: 'Success',
        description: 'Document downloaded successfully',
      });

      // Refresh to update download count
      fetchDocuments();
    } catch (error) {
      console.error('Error downloading document:', error);
      toast({
        title: 'Error',
        description: 'Failed to download document',
        variant: 'destructive',
      });
    } finally {
      setDownloadingId(null);
    }
  };

  // Handle view
  const handleView = (document: DocumentListItem) => {
    setSelectedDocument(document);
    setIsDetailOpen(true);
  };

  // Handle acknowledge
  const handleAcknowledge = async (document: DocumentListItem) => {
    try {
      await documentService.acknowledgeDocument(document.id);
      toast({
        title: 'Success',
        description: 'Document acknowledged successfully',
      });
      await Promise.all([fetchDocuments(), fetchSummary()]);

      // Update selected document if viewing
      if (selectedDocument?.id === document.id) {
        setSelectedDocument({
          ...selectedDocument,
          has_acknowledged: true,
        });
      }
    } catch (error) {
      console.error('Error acknowledging document:', error);
      toast({
        title: 'Error',
        description: 'Failed to acknowledge document',
        variant: 'destructive',
      });
    }
  };

  // Handle filter changes
  const handleFileTypeChange = (value: string) => {
    setFileTypeFilter(value === 'all' ? '' : value);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <FolderOpen className="h-6 w-6" />
          Documents
        </h1>
        <p className="text-muted-foreground">
          Access company documents, policies, and forms
        </p>
      </div>

      {/* Summary Cards */}
      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-20" />
          ))}
        </div>
      ) : (
        summary && (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <SummaryCard
              title="Total Documents"
              count={summary.total_documents}
              icon={<FileText className="h-5 w-5 text-blue-600" />}
              color="bg-blue-100"
            />
            <SummaryCard
              title="Categories"
              count={summary.total_categories}
              icon={<FolderOpen className="h-5 w-5 text-purple-600" />}
              color="bg-purple-100"
            />
            <SummaryCard
              title="Pending Acknowledgements"
              count={summary.pending_acknowledgements}
              icon={<AlertCircle className="h-5 w-5 text-orange-600" />}
              color="bg-orange-100"
            />
          </div>
        )
      )}

      {/* Pending Acknowledgements Alert */}
      {summary && summary.pending_acknowledgements > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="p-4 flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-orange-600" />
            <div>
              <p className="font-medium text-orange-800">
                {summary.pending_acknowledgements} document
                {summary.pending_acknowledgements !== 1 ? 's' : ''} require your
                acknowledgement
              </p>
              <p className="text-sm text-orange-700">
                Please review and acknowledge the documents marked with "Pending"
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Documents List */}
      <DocumentsList
        documents={documents}
        categories={categories}
        fileTypes={fileTypes}
        isLoading={isLoading}
        searchQuery={searchQuery}
        categoryFilter={categoryFilter}
        fileTypeFilter={fileTypeFilter}
        onSearchChange={setSearchQuery}
        onCategoryChange={setCategoryFilter}
        onFileTypeChange={handleFileTypeChange}
        onDownload={handleDownload}
        onView={handleView}
        onAcknowledge={handleAcknowledge}
        onRefresh={fetchDocuments}
        downloadingId={downloadingId}
      />

      {/* Document Detail Modal */}
      <Dialog open={isDetailOpen} onOpenChange={setIsDetailOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Document Details
            </DialogTitle>
          </DialogHeader>

          {selectedDocument && (
            <div className="space-y-4">
              {/* Title and badges */}
              <div>
                <h3 className="font-semibold text-lg">{selectedDocument.title}</h3>
                <div className="flex flex-wrap gap-2 mt-2">
                  <Badge variant="outline">{selectedDocument.category_name}</Badge>
                  <Badge variant="outline">
                    {selectedDocument.file_type.toUpperCase()}
                  </Badge>
                  <Badge variant="outline">v{selectedDocument.version}</Badge>
                  {selectedDocument.requires_acknowledgement && (
                    <Badge
                      variant="outline"
                      className={
                        selectedDocument.has_acknowledged
                          ? 'bg-green-100 text-green-700'
                          : 'bg-orange-100 text-orange-700'
                      }
                    >
                      {selectedDocument.has_acknowledged ? (
                        <>
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Acknowledged
                        </>
                      ) : (
                        <>
                          <AlertCircle className="h-3 w-3 mr-1" />
                          Pending
                        </>
                      )}
                    </Badge>
                  )}
                </div>
              </div>

              {/* Description */}
              {selectedDocument.description && (
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground">
                    Description
                  </h4>
                  <p className="text-sm mt-1">{selectedDocument.description}</p>
                </div>
              )}

              {/* Meta info */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">File Size:</span>
                  <p>{selectedDocument.file_size_display}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Downloads:</span>
                  <p>{selectedDocument.download_count}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Created:</span>
                  <p>
                    {format(new Date(selectedDocument.created_at), 'MMM d, yyyy')}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Updated:</span>
                  <p>
                    {format(new Date(selectedDocument.updated_at), 'MMM d, yyyy')}
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-4 border-t">
                {selectedDocument.file_url && (
                  <Button
                    variant="outline"
                    onClick={() => window.open(selectedDocument.file_url!, '_blank')}
                  >
                    <ExternalLink className="h-4 w-4 mr-1" />
                    Open in New Tab
                  </Button>
                )}
                <Button onClick={() => handleDownload(selectedDocument)}>
                  <Download className="h-4 w-4 mr-1" />
                  Download
                </Button>
                {selectedDocument.requires_acknowledgement &&
                  !selectedDocument.has_acknowledged && (
                    <Button
                      variant="default"
                      onClick={() => handleAcknowledge(selectedDocument)}
                    >
                      <CheckCircle className="h-4 w-4 mr-1" />
                      Acknowledge
                    </Button>
                  )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default DocumentsPage;
