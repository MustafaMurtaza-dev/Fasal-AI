import axios from 'axios';

const API = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  timeout: 120000,
});

export const advisoryAPI = {
  ask: async (query: string, cropType?: string, location?: string) => {
    const res = await API.post('/advisory/ask', {
      query,
      crop_type: cropType || null,
      location: location || null,
      language: 'ur',
      context: null,
    });

    // 🔍 DEBUG — browser console mein check karein
    console.log('📦 RAW API Response:', JSON.stringify(res.data, null, 2));

    return res.data;
  },
};

export const diagnosisAPI = {
  uploadImage: async (file: File, cropType?: string, location?: string) => {
    const fd = new FormData();
    fd.append('image', file);
    if (cropType) fd.append('crop_type', cropType);
    if (location) fd.append('location', location);
    return (await API.post('/diagnosis/image', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })).data;
  },
  symptoms: async (cropType: string, symptoms: string) => {
    const fd = new FormData();
    fd.append('crop_type', cropType);
    fd.append('symptoms', symptoms);
    return (await API.post('/diagnosis/symptoms', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })).data;
  },
};

export const marketAPI = {
  predict: async (crop: string, days = 7) =>
    (await API.get(`/market/predict/${crop}`, { params: { days } })).data,
  current: async (crop: string) =>
    (await API.get(`/market/current/${crop}`)).data,
};

export const weatherAPI = {
  current: async (city = 'Lahore') =>
    (await API.get('/weather/current', { params: { city } })).data,
  cropImpact: async (city: string, crop: string) =>
    (await API.get('/weather/crop-impact', { params: { city, crop } })).data,
  alerts: async (city: string, crop: string) =>
    (await API.get('/weather/alerts', { params: { city, crop } })).data,
};

export const farmAPI = {
  calendar: async (province: string, crop: string) =>
    (await API.get(`/farm/calendar/${province}/${crop}`)).data,
  crops: async () => (await API.get('/farm/crops')).data,
};

export default API;