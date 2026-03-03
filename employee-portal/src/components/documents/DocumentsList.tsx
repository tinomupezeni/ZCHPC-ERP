import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { FolderOpen, Search, RefreshCw, Filter } from 'lucide-react';
import { DocumentCard } from './DocumentCard';
import type { DocumentListItem, DocumentCategory } from '@/types/document.types';

interface DocumentsListProps {
  documents: DocumentListItem[];
  categories: DocumentCategory[];
  fileTypes: string[];
  isLoading: boolean;
  searchQuery: string;
  categoryFilter: number | null;
  fileTypeFilter: string;
  onSearchChange: (value: string) => void;
  onCategoryChange: (value: number | null) => void;
  onFileTypeChange: (value: string) => void;
  onDownload: (document: DocumentListItem) => void;
  onView: (document: DocumentListItem) => void;
  onAcknowledge: (document: DocumentListItem) => void;
  onRefresh: () => void;
  downloadingId: number | null;
}

export function DocumentsList({
  documents,
  categories,
  fileTypes,
  isLoading,
  searchQuery,
  categoryFilter,
  fileTypeFilter,
  onSearchChange,
  onCategoryChange,
  onFileTypeChange,
  onDownload,
  onView,
  onAcknowledge,
  onRefresh,
  downloadingId,
}: DocumentsListProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <FolderOpen className="h-5 w-5" />
            Documents
          </CardTitle>
          <Button variant="outline" size="sm" onClick={onRefresh}>
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </Button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3 mt-4">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-9"
            />
          </div>

          {/* Category filter */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <Select
              value={categoryFilter?.toString() || 'all'}
              onValueChange={(v) =>
                onCategoryChange(v === 'all' ? null : parseInt(v))
              }
            >
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat.id} value={cat.id.toString()}>
                    {cat.name} ({cat.document_count})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* File type filter */}
          <Select value={fileTypeFilter || 'all'} onValueChange={onFileTypeChange}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              {fileTypes.map((type) => (
                <SelectItem key={type} value={type}>
                  {type.toUpperCase()}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-32 w-full" />
            ))}
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FolderOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No documents found</p>
            <p className="text-sm">
              {searchQuery || categoryFilter || fileTypeFilter
                ? 'Try adjusting your filters'
                : 'No documents available at this time'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {documents.map((doc) => (
              <DocumentCard
                key={doc.id}
                document={doc}
                onDownload={onDownload}
                onView={onView}
                onAcknowledge={onAcknowledge}
                isDownloading={downloadingId === doc.id}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default DocumentsList;
