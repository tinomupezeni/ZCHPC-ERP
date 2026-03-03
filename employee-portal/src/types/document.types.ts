export interface DocumentCategory {
  id: number;
  name: string;
  description: string;
  icon: string;
  document_count: number;
}

export interface DocumentListItem {
  id: number;
  title: string;
  description: string;
  category: number;
  category_name: string;
  file_type: string;
  file_size: number;
  file_size_display: string;
  file_url: string | null;
  version: string;
  requires_acknowledgement: boolean;
  has_acknowledged: boolean;
  download_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentDetail extends DocumentListItem {
  uploaded_by_name: string | null;
  acknowledgement_count: number;
}

export interface DocumentAcknowledgement {
  id: number;
  document: number;
  employee_name: string;
  acknowledged_at: string;
}

export interface DocumentSummary {
  total_documents: number;
  total_categories: number;
  pending_acknowledgements: number;
  recent_documents: DocumentListItem[];
}
