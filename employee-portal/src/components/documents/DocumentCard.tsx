import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  FileText,
  FileSpreadsheet,
  FileImage,
  File,
  Download,
  Eye,
  CheckCircle,
  AlertCircle,
  Clock,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import type { DocumentListItem } from '@/types/document.types';

interface DocumentCardProps {
  document: DocumentListItem;
  onDownload: (document: DocumentListItem) => void;
  onView: (document: DocumentListItem) => void;
  onAcknowledge?: (document: DocumentListItem) => void;
  isDownloading?: boolean;
}

const fileTypeIcons: Record<string, React.ReactNode> = {
  pdf: <FileText className="h-8 w-8 text-red-500" />,
  doc: <FileText className="h-8 w-8 text-blue-500" />,
  docx: <FileText className="h-8 w-8 text-blue-500" />,
  xls: <FileSpreadsheet className="h-8 w-8 text-green-500" />,
  xlsx: <FileSpreadsheet className="h-8 w-8 text-green-500" />,
  csv: <FileSpreadsheet className="h-8 w-8 text-green-600" />,
  png: <FileImage className="h-8 w-8 text-purple-500" />,
  jpg: <FileImage className="h-8 w-8 text-purple-500" />,
  jpeg: <FileImage className="h-8 w-8 text-purple-500" />,
  gif: <FileImage className="h-8 w-8 text-purple-500" />,
};

const fileTypeBadgeColors: Record<string, string> = {
  pdf: 'bg-red-100 text-red-700',
  doc: 'bg-blue-100 text-blue-700',
  docx: 'bg-blue-100 text-blue-700',
  xls: 'bg-green-100 text-green-700',
  xlsx: 'bg-green-100 text-green-700',
  csv: 'bg-green-100 text-green-700',
  png: 'bg-purple-100 text-purple-700',
  jpg: 'bg-purple-100 text-purple-700',
  jpeg: 'bg-purple-100 text-purple-700',
};

export function DocumentCard({
  document,
  onDownload,
  onView,
  onAcknowledge,
  isDownloading,
}: DocumentCardProps) {
  const icon = fileTypeIcons[document.file_type] || (
    <File className="h-8 w-8 text-gray-500" />
  );
  const badgeColor =
    fileTypeBadgeColors[document.file_type] || 'bg-gray-100 text-gray-700';

  const needsAcknowledgement =
    document.requires_acknowledgement && !document.has_acknowledged;

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex gap-4">
          {/* File icon */}
          <div className="flex-shrink-0 p-2 bg-muted rounded-lg">{icon}</div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Title and badges */}
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <h3 className="font-medium text-sm truncate">{document.title}</h3>
                <p className="text-xs text-muted-foreground truncate">
                  {document.category_name}
                </p>
              </div>
              <div className="flex gap-1 flex-shrink-0">
                <Badge variant="outline" className={badgeColor}>
                  {document.file_type.toUpperCase()}
                </Badge>
                {needsAcknowledgement && (
                  <Badge variant="outline" className="bg-orange-100 text-orange-700">
                    <AlertCircle className="h-3 w-3 mr-1" />
                    Pending
                  </Badge>
                )}
                {document.has_acknowledged && document.requires_acknowledgement && (
                  <Badge variant="outline" className="bg-green-100 text-green-700">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Acknowledged
                  </Badge>
                )}
              </div>
            </div>

            {/* Description */}
            {document.description && (
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                {document.description}
              </p>
            )}

            {/* Meta info */}
            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
              <span>{document.file_size_display}</span>
              <span>v{document.version}</span>
              <span className="flex items-center gap-1">
                <Download className="h-3 w-3" />
                {document.download_count}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatDistanceToNow(new Date(document.updated_at), {
                  addSuffix: true,
                })}
              </span>
            </div>

            {/* Actions */}
            <div className="flex gap-2 mt-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onView(document)}
              >
                <Eye className="h-4 w-4 mr-1" />
                View
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDownload(document)}
                disabled={isDownloading}
              >
                <Download className="h-4 w-4 mr-1" />
                Download
              </Button>
              {needsAcknowledgement && onAcknowledge && (
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => onAcknowledge(document)}
                >
                  <CheckCircle className="h-4 w-4 mr-1" />
                  Acknowledge
                </Button>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default DocumentCard;
