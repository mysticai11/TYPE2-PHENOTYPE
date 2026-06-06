import { useState } from 'react';
import { getQuadrantCounterfactual } from '../api/client';

export const useCounterfactual = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCounterfactual = async (biomarkers) => {
    setLoading(true);
    setError(null);
    try {
      const result = await getQuadrantCounterfactual(biomarkers);
      setData(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, fetchCounterfactual };
};
