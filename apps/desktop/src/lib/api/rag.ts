import { api } from "./client";

export interface RagDocument {
  id: string;
  filename: string;
  title: string;
  mime_type: string;
  entity_type: string | null;
  entity_id: string | null;
  created_at: string;
}

export const fetchRagDocuments = () => api.get<RagDocument[]>("/api/rag/documents");
