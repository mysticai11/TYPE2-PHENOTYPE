import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

export const inferMetabolicState = async (biomarkers) => {
  const response = await api.post('/infer', biomarkers);
  return response.data;
};

export const getQuadrantCounterfactual = async (biomarkers) => {
  const response = await api.post(`/quadrant_counterfactual`, biomarkers);
  return response.data;
};
