import { useState } from "react";
import axios from "axios";

export default function Home() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [loading, setLoading] = useState(false);
  const [zipUrl, setZipUrl] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!files || files.length === 0) return;

    const formData = new FormData();
    Array.from(files).forEach((file) => formData.append("files", file));

    setLoading(true);
    setZipUrl(null);
    try {
      const res = await axios.post(
        "https://image-trim-api.up.railway.app/batch-trim-zip/", // 必要に応じてURL変更
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          responseType: "blob",
        }
      );
      const blob = new Blob([res.data], { type: "application/zip" });
      const url = URL.createObjectURL(blob);
      setZipUrl(url);
    } catch (err) {
      console.error("Upload failed", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
      <h1 className="text-3xl font-bold mb-6">画像トリミングツール</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4 items-center">
        <input
          type="file"
          multiple
          accept="image/*"
          onChange={(e) => setFiles(e.target.files)}
          className="border p-2 rounded bg-white"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          {loading ? "処理中..." : "一括トリミング&ZIPダウンロード"}
        </button>
      </form>
      {zipUrl && (
        <a
          href={zipUrl}
          download="trimmed_images.zip"
          className="mt-6 text-blue-600 underline"
        >
          ダウンロードはこちら
        </a>
      )}
    </main>
  );
}