import { useState } from 'react';
import { inferMetabolicState } from '../api/client';

export const useInference = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const infer = async (biomarkers) => {
    setLoading(true);
    setError(null);
    try {
      const result = await inferMetabolicState(biomarkers);
      setData(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, infer };
};
