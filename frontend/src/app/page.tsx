'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Home() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [loading, setLoading] = useState(false);
  const [zipUrl, setZipUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [focus, setFocus] = useState<'full' | 'upper' | 'lower'>('full');

  useEffect(() => {
    return () => {
      if (zipUrl) URL.revokeObjectURL(zipUrl);
    };
  }, [zipUrl]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!files || files.length === 0) {
      setError('画像ファイルを選択してください。');
      return;
    }

    const formData = new FormData();
    Array.from(files).forEach((file) => formData.append('files', file));

    setLoading(true);
    setError(null);
    setZipUrl(null);

    try {
      const res = await axios.post(
        `https://web-production-a74c.up.railway.app/batch-trim-zip/?focus=${focus}`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          responseType: 'blob',
        }
      );

      const blob = new Blob([res.data], { type: 'application/zip' });
      const url = URL.createObjectURL(blob);
      setZipUrl(url);
    } catch (err) {
      console.error('Upload failed', err);
      setError('アップロードに失敗しました。もう一度お試しください。');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-950 to-purple-900 text-white flex flex-col items-center justify-center px-4 py-12 font-sans">
      <div className="w-full max-w-xl p-8 bg-gray-900 bg-opacity-70 rounded-2xl shadow-2xl border border-blue-400">
        <h1 className="text-3xl font-bold text-center mb-6 text-purple-300">AI画像トリミング</h1>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div>
            <label className="block text-sm font-medium mb-1">画像ファイルを選択（複数可）</label>
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={(e) => setFiles(e.target.files)}
              className="file:border-2 file:border-purple-400 file:px-3 file:py-1 file:rounded file:bg-purple-800 file:text-white text-sm bg-gray-800 text-gray-100 w-full"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">フォーカス対象</label>
            <select
              value={focus}
              onChange={(e) => setFocus(e.target.value as 'full' | 'upper' | 'lower')}
              className="bg-gray-800 text-white border border-purple-500 rounded px-3 py-2 w-full"
            >
              <option value="full">通常（全体）</option>
              <option value="upper">トップス重視</option>
              <option value="lower">スカート・パンツ重視</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`px-4 py-2 rounded font-medium transition text-white bg-gradient-to-r from-blue-700 to-purple-700 hover:from-blue-600 hover:to-purple-600 ${loading ? 'opacity-60 cursor-not-allowed' : ''}`}
          >
            {loading ? '処理中...' : '一括トリミングしてZIPを作成'}
          </button>
        </form>

        {error && (
          <p className="mt-4 text-sm text-red-400 text-center">{error}</p>
        )}

        {zipUrl && (
          <div className="mt-6 text-center">
            <a
              href={zipUrl}
              download="trimmed_images.zip"
              className="inline-block text-blue-300 hover:underline"
            >
              ✅ ダウンロードはこちら
            </a>
          </div>
        )}
      </div>
    </main>
  );
}