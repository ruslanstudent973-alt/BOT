import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { Send, Image as ImageIcon, Clock, DollarSign, Users, CheckCircle } from 'lucide-react';

const PRESET_DESCRIPTIONS = [
  "🔥 Tezkor sotuv! Yangi mahsulot keldi. Sifati a'lo darajada.",
  "✨ Eksklyuziv taklif! Faqat bugun uchun maxsus chegirma.",
  "📦 Sifatli va hamyonbop mahsulot. Yetkazib berish bepul!",
  "🌟 Siz kutgan mahsulot endi sotuvda! Shoshiling, soni cheklangan.",
  "💎 Premium sifat, hamyonbop narx. O'zingizga munosibini tanlang!"
];

const App = () => {
  const [description, setDescription] = useState(PRESET_DESCRIPTIONS[0]);
  const [price, setPrice] = useState('');
  const [time, setTime] = useState('');
  const [groupId, setGroupId] = useState('');
  const [images, setImages] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    // Initialize Telegram WebApp
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
    }
  }, []);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files).slice(0, 5);
      setImages(selectedFiles);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!groupId || !price || !time) {
      alert("Iltimos, barcha maydonlarni to'ldiring!");
      return;
    }

    setLoading(true);
    
    // Prepare form data
    const formData = new FormData();
    formData.append('description', description);
    formData.append('price', price);
    formData.append('time', time);
    formData.append('groupId', groupId);
    images.forEach((img, index) => {
      formData.append(`image_${index}`, img);
    });

    try {
      const response = await fetch('/api/post', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        setSuccess(true);
        setTimeout(() => setSuccess(false), 3000);
      } else {
        const data = await response.json();
        alert(`Xato: ${data.error || 'Noma\'lum xato'}`);
      }
    } catch (error) {
      console.error(error);
      alert("Serverga ulanishda xato!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-100 p-4 font-sans text-neutral-900">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mx-auto max-w-md overflow-hidden rounded-3xl bg-white shadow-xl"
      >
        <div className="bg-neutral-900 p-6 text-white">
          <h1 className="text-2xl font-bold tracking-tight">Post Generator</h1>
          <p className="text-sm text-neutral-400">Guruhga post yuborish va pin qilish</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 p-6">
          {/* Group ID */}
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-500">
              <Users size={14} /> Guruh ID (masalan: -100...)
            </label>
            <input 
              type="text" 
              value={groupId}
              onChange={(e) => setGroupId(e.target.value)}
              placeholder="Guruh ID sini kiriting"
              className="w-full rounded-xl border border-neutral-200 bg-neutral-50 p-3 outline-none focus:border-neutral-900 focus:ring-1 focus:ring-neutral-900"
            />
          </div>

          {/* Description Selection */}
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-500">
              Tavsifni tanlang
            </label>
            <div className="flex flex-wrap gap-2">
              {PRESET_DESCRIPTIONS.map((desc, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setDescription(desc)}
                  className={`rounded-full px-4 py-2 text-xs transition-all ${
                    description === desc 
                    ? 'bg-neutral-900 text-white shadow-md' 
                    : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'
                  }`}
                >
                  Variant {idx + 1}
                </button>
              ))}
            </div>
            <textarea 
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="mt-2 h-24 w-full rounded-xl border border-neutral-200 bg-neutral-50 p-3 outline-none focus:border-neutral-900 focus:ring-1 focus:ring-neutral-900"
            />
          </div>

          {/* Price and Time */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-500">
                <DollarSign size={14} /> Narxi
              </label>
              <input 
                type="text" 
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="Masalan: 50,000"
                className="w-full rounded-xl border border-neutral-200 bg-neutral-50 p-3 outline-none focus:border-neutral-900 focus:ring-1 focus:ring-neutral-900"
              />
            </div>
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-500">
                <Clock size={14} /> Vaqti
              </label>
              <input 
                type="text" 
                value={time}
                onChange={(e) => setTime(e.target.value)}
                placeholder="Masalan: 12:00"
                className="w-full rounded-xl border border-neutral-200 bg-neutral-50 p-3 outline-none focus:border-neutral-900 focus:ring-1 focus:ring-neutral-900"
              />
            </div>
          </div>

          {/* Image Upload */}
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-500">
              <ImageIcon size={14} /> Rasmlar (4-5 ta)
            </label>
            <div className="relative">
              <input 
                type="file" 
                multiple 
                accept="image/*"
                onChange={handleImageChange}
                className="hidden"
                id="image-upload"
              />
              <label 
                htmlFor="image-upload"
                className="flex cursor-pointer items-center justify-center gap-2 rounded-xl border-2 border-dashed border-neutral-200 bg-neutral-50 p-6 transition-all hover:border-neutral-400 hover:bg-neutral-100"
              >
                <ImageIcon className="text-neutral-400" />
                <span className="text-sm text-neutral-500">
                  {images.length > 0 ? `${images.length} ta rasm tanlandi` : 'Rasmlarni tanlang'}
                </span>
              </label>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || success}
            className={`flex w-full items-center justify-center gap-2 rounded-2xl p-4 font-bold transition-all ${
              success 
              ? 'bg-green-500 text-white' 
              : 'bg-neutral-900 text-white hover:bg-neutral-800 active:scale-95'
            }`}
          >
            {loading ? (
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : success ? (
              <> <CheckCircle size={20} /> Yuborildi! </>
            ) : (
              <> <Send size={20} /> Yuborish va Pin qilish </>
            )}
          </button>
        </form>
      </motion.div>
    </div>
  );
};

export default App;
