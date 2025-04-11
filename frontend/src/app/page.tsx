'use client';

import { useState, useEffect } from "react";
import axios from "axios";

export default function Home() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [loading, setLoading] = useState(false);
  const [zipUrl, setZipUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      if (zipUrl) {
        URL.revokeObjectURL(zipUrl);
      }
    };
  }, [zipUrl]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!files || files.length === 0) {
      setError("画像ファイルを選択してください。");
      return;
    }

    const formData = new FormData();
    Array.from(files).forEach((file) => formData.append("files", file));

    setLoading(true);
    setError(null);
    setZipUrl(null);

    try {
      const res = await axios.post(
        "https://web-production-a74c.up.railway.app/batch-trim-zip/",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
          responseType: "blob",
        }
      );

      const blob = new Blob([res.data], { type: "application/zip" });
      const url = URL.createObjectURL(blob);
      setZipUrl(url);
    } catch (err) {
      console.error("Upload failed", err);
      setError("アップロードに失敗しました。もう一度お試しください。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-100 flex flex-col items-center justify-center px-4 py-8">
      <div className="w-full max-w-md p-6 bg-white dark:bg-gray-800 rounded-2xl shadow-lg">
        <h1 className="text-2xl font-semibold text-center mb-6">画像トリミングツール</h1>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <label className="text-sm font-medium">画像を選択（複数可）</label>
          <input
            type="file"
            multiple
            accept="image/*"
            onChange={(e) => setFiles(e.target.files)}
            className="file:border file:border-gray-300 file:px-3 file:py-1 file:rounded file:bg-blue-50 file:text-blue-700 text-sm"
            disabled={loading}
          />

          <button
            type="submit"
            disabled={loading}
            className={`px-4 py-2 rounded font-medium text-white transition ${
              loading
                ? "bg-blue-300 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {loading ? "処理中..." : "一括トリミングしてZIPを作成"}
          </button>
        </form>

        {error && (
          <p className="mt-4 text-sm text-red-500 text-center">{error}</p>
        )}

        {zipUrl && (
          <div className="mt-6 text-center">
            <a
              href={zipUrl}
              download="trimmed_images.zip"
              className="inline-block text-blue-600 dark:text-blue-400 hover:underline"
            >
              ✅ ダウンロードはこちら
            </a>
          </div>
        )}
      </div>
    </main>
  );
}
