import api from './api';
import type {
  DocumentCategory,
  DocumentListItem,
  DocumentDetail,
  DocumentAcknowledgement,
  DocumentSummary,
} from '@/types/document.types';

export const documentService = {
  /**
   * Get all document categories
   */
  async getCategories(): Promise<DocumentCategory[]> {
    const response = await api.get<DocumentCategory[]>('/portal/documents/categories/');
    return response.data;
  },

  /**
   * Get list of documents with optional filters
   */
  async getDocuments(params?: {
    category?: number;
    file_type?: string;
    search?: string;
  }): Promise<DocumentListItem[]> {
    const response = await api.get<DocumentListItem[]>('/portal/documents/', {
      params,
    });
    return response.data;
  },

  /**
   * Get document details
   */
  async getDocument(id: number): Promise<DocumentDetail> {
    const response = await api.get<DocumentDetail>(`/portal/documents/${id}/`);
    return response.data;
  },

  /**
   * Download a document
   */
  async downloadDocument(id: number): Promise<Blob> {
    const response = await api.get(`/portal/documents/${id}/download/`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Acknowledge reading a document
   */
  async acknowledgeDocument(id: number): Promise<DocumentAcknowledgement> {
    const response = await api.post<DocumentAcknowledgement>(
      `/portal/documents/${id}/acknowledge/`
    );
    return response.data;
  },

  /**
   * Get documents summary
   */
  async getSummary(): Promise<DocumentSummary> {
    const response = await api.get<DocumentSummary>('/portal/documents/summary/');
    return response.data;
  },

  /**
   * Get documents pending acknowledgement
   */
  async getPendingAcknowledgements(): Promise<DocumentListItem[]> {
    const response = await api.get<DocumentListItem[]>(
      '/portal/documents/pending_acknowledgements/'
    );
    return response.data;
  },

  /**
   * Get available file types for filtering
   */
  async getFileTypes(): Promise<string[]> {
    const response = await api.get<string[]>('/portal/documents/file_types/');
    return response.data;
  },
};

export default documentService;
