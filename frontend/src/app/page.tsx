'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [focus, setFocus] = useState<'full' | 'upper' | 'lower'>('full');

  useEffect(() => {
    return () => {
      if (imageUrl) URL.revokeObjectURL(imageUrl);
    };
  }, [imageUrl]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('画像ファイルを選択してください。');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    setError(null);
    setImageUrl(null);

    try {
      const res = await axios.post(
        `https://web-production-a74c.up.railway.app/trim-single/?focus=${focus}`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
        }
      );

      const url = `https://web-production-a74c.up.railway.app${res.data.image_url}`;
      setImageUrl(url);
    } catch (err) {
      console.error('Upload failed', err);
      setError('アップロードに失敗しました。もう一度お試しください。');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-950 to-purple-900 text-white flex flex-col items-center justify-center px-4 py-8 font-sans">
      <div className="w-full max-w-md p-6 bg-gray-900 bg-opacity-70 rounded-2xl shadow-2xl border border-blue-400">
        <h1 className="text-3xl font-bold text-center mb-6 text-purple-300">AI画像トリミング</h1>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <label className="text-sm font-medium">画像ファイルを選択（1枚）</label>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="file:border-2 file:border-purple-400 file:px-3 file:py-1 file:rounded file:bg-purple-800 file:text-white text-sm bg-gray-800 text-gray-100"
            disabled={loading}
          />

          <label className="text-sm font-medium">フォーカス対象</label>
          <select
            value={focus}
            onChange={(e) => setFocus(e.target.value as 'full' | 'upper' | 'lower')}
            className="bg-gray-800 text-white border border-purple-500 rounded px-3 py-2"
          >
            <option value="full">通常（全体）</option>
            <option value="upper">トップス重視</option>
            <option value="lower">スカート・パンツ重視</option>
          </select>

          <button
            type="submit"
            disabled={loading}
            className={`px-4 py-2 rounded font-medium transition text-white bg-gradient-to-r from-blue-700 to-purple-700 hover:from-blue-600 hover:to-purple-600 ${loading ? 'opacity-60 cursor-not-allowed' : ''}`}
          >
            {loading ? '処理中...' : '画像トリミングを実行'}
          </button>
        </form>

        {error && (
          <p className="mt-4 text-sm text-red-400 text-center">{error}</p>
        )}

        {imageUrl && (
          <div className="mt-6 text-center">
            <img
              src={imageUrl}
              alt="Trimmed"
              className="mx-auto rounded-lg border border-purple-300 max-h-[450px]"
            />
            <a
              href={imageUrl}
              download="trimmed_image.png"
              className="mt-2 inline-block text-blue-300 hover:underline"
            >
              ✅ ダウンロードはこちら
            </a>
          </div>
        )}
      </div>
    </main>
  );
}
