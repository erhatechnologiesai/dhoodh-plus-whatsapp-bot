'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Upload,
  BookOpen,
  FileText,
  Trash2,
  RefreshCw,
  CheckCircle2,
  Clock,
  Eye,
  Layers,
  Sparkles,
  X
} from 'lucide-react';
import { Header } from '@/components/Header';
import { api, DocumentItem, DocumentChunk } from '@/lib/api';
import { formatBytes, formatFullDate } from '@/lib/utils';

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedDocChunks, setSelectedDocChunks] = useState<DocumentChunk[] | null>(null);
  const [activeDocName, setActiveDocName] = useState<string>('');
  const [loadingChunks, setLoadingChunks] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDocuments = async () => {
    try {
      const data = await api.listDocuments();
      setDocuments(data);
    } catch (err) {
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
    const interval = setInterval(loadDocuments, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Only PDF files are supported.');
      return;
    }

    setUploading(true);
    try {
      await api.uploadDocument(file);
      await loadDocuments();
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      console.error('Upload failed:', err);
      alert('Failed to upload PDF. Please check server logs.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete "${name}"? This will permanently remove its embeddings.`)) {
      return;
    }
    try {
      await api.deleteDocument(id);
      await loadDocuments();
      if (selectedDocChunks && activeDocName === name) {
        setSelectedDocChunks(null);
      }
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  const handleInspectChunks = async (doc: DocumentItem) => {
    setActiveDocName(doc.name);
    setLoadingChunks(true);
    try {
      const chunks = await api.getDocumentChunks(doc.id);
      setSelectedDocChunks(chunks);
    } catch (err) {
      console.error('Failed to load chunks:', err);
    } finally {
      setLoadingChunks(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 text-black">
      <Header
        title="Knowledge Base"
        subtitle="6-Page Verified PDF Handbook & Embeddings"
      />

      <main className="flex-1 px-4 md:px-8 pb-8 space-y-6 overflow-y-auto text-black">
        {/* Upload Card */}
        <div className="coachpro-card rounded-[26px] p-6 sm:p-8 text-center border-2 border-dashed border-teal-300 hover:border-teal-600 transition-colors text-black">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf"
            className="hidden"
          />
          <div className="w-14 h-14 bg-teal-100 text-black rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-sm font-bold">
            <Upload className="w-7 h-7 text-black" />
          </div>
          <h3 className="font-black text-black text-lg">Upload Knowledge PDF</h3>
          <p className="text-black text-xs font-bold mt-1 max-w-md mx-auto leading-relaxed">
            Upload product manuals, veterinary guides, or pricing sheets. The ingestion engine automatically extracts text, chunks semantically, and stores embeddings.
          </p>
          <div className="mt-5 flex items-center justify-center gap-3">
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="px-6 py-2.5 bg-gradient-to-r from-teal-800 to-emerald-600 hover:opacity-95 disabled:opacity-50 text-white font-black rounded-2xl text-xs transition-all shadow-md flex items-center gap-2"
            >
              {uploading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Processing Document...</span>
                </>
              ) : (
                <>
                  <Upload className="w-3.5 h-3.5" />
                  <span>Select PDF File</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Documents Table */}
        <div className="coachpro-card rounded-[26px] p-6 shadow-sm overflow-hidden text-black">
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-200">
            <div>
              <h4 className="font-black text-black text-base">Indexed Documents</h4>
              <p className="text-xs text-black font-bold">Live vector database index status</p>
            </div>
            <button
              onClick={loadDocuments}
              className="p-2 text-black hover:bg-slate-200 rounded-xl transition-colors"
            >
              <RefreshCw className={`w-4 h-4 text-black ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {documents.length === 0 ? (
            <div className="py-12 text-center text-black">
              <BookOpen className="w-10 h-10 mx-auto mb-2 text-black" />
              <p className="text-sm font-black text-black">No external documents uploaded.</p>
              <p className="text-xs text-black font-bold mt-1">
                The authoritative 6-Page Doodh Plus Handbook is active in the engine.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto text-black">
              <table className="w-full text-left text-xs text-black">
                <thead>
                  <tr className="border-b-2 border-slate-200 text-[11px] font-black text-black uppercase tracking-wider">
                    <th className="py-3 px-3">DOCUMENT</th>
                    <th className="py-3 px-3">CHUNKS</th>
                    <th className="py-3 px-3">SIZE</th>
                    <th className="py-3 px-3">STATUS</th>
                    <th className="py-3 px-3 text-right">ACTIONS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 text-black">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-teal-50/50 transition-colors text-black">
                      <td className="py-3.5 px-3">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-xl bg-teal-100 text-black flex items-center justify-center font-bold">
                            <FileText className="w-4 h-4 text-black" />
                          </div>
                          <div>
                            <span className="font-black text-black block">{doc.name}</span>
                            <span className="text-[10px] text-black font-mono font-bold">
                              {formatFullDate(doc.created_at)}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 px-3 font-black text-black">
                        {doc.chunks_count ?? doc.chunk_count ?? 0} chunks
                      </td>
                      <td className="py-3.5 px-3 text-black font-mono font-bold">
                        {formatBytes(doc.file_size)}
                      </td>
                      <td className="py-3.5 px-3">
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-black bg-emerald-100 text-black border border-emerald-300">
                          <CheckCircle2 className="w-3 h-3 text-emerald-700" />
                          {doc.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-3 text-right space-x-2">
                        <button
                          onClick={() => handleInspectChunks(doc)}
                          className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-teal-100 text-black font-black text-xs transition-colors"
                        >
                          Inspect Chunks
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id, doc.name)}
                          className="p-1.5 rounded-xl text-black hover:bg-rose-100 transition-colors"
                          title="Delete Document"
                        >
                          <Trash2 className="w-4 h-4 text-black" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Chunks Inspector Modal */}
        {selectedDocChunks && (
          <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 text-black">
            <div className="bg-white rounded-[28px] max-w-2xl w-full p-6 shadow-2xl border border-white max-h-[85vh] flex flex-col text-black">
              <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-4">
                <div>
                  <h4 className="font-black text-base text-black">
                    Semantic Chunks: {activeDocName}
                  </h4>
                  <p className="text-xs text-black font-bold">
                    {selectedDocChunks.length} vector embeddings indexed
                  </p>
                </div>
                <button
                  onClick={() => setSelectedDocChunks(null)}
                  className="p-2 rounded-xl text-black hover:bg-slate-100"
                >
                  <X className="w-5 h-5 text-black" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto space-y-3 pr-2 text-black">
                {selectedDocChunks.map((chunk, idx) => (
                  <div key={idx} className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-black">
                    <span className="font-black text-black text-[10px] uppercase block mb-1">
                      Chunk #{idx + 1}
                    </span>
                    <p className="text-black leading-relaxed font-bold whitespace-pre-line">
                      {chunk.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
