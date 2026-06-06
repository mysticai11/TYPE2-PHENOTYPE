import { useState } from "react";

export function BiomarkerForm({ onSubmit, loading }) {
  const [formData, setFormData] = useState({
    fasting_glucose_mg_dL: 90,
    fasting_insulin_uU_mL: 10,
    triglycerides_mg_dL: 100,
    hdl_mg_dL: 50,
    ast_U_L: 20,
    alt_U_L: 25,
    ggt_U_L: 25,
    bmi: 23.5,
    waist_cm: 85,
    platelets_1000_uL: 250,
    age: 45,
    sex: 1,
    ancestry_proxy: 1,
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: parseFloat(value) }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="form-grid">
      {Object.keys(formData).map((key) => (
        <div key={key} className="input-group">
          <label>{key.replace(/_/g, " ")}</label>
          <input
            type="number"
            step="0.1"
            name={key}
            value={formData[key]}
            onChange={handleChange}
            required
          />
        </div>
      ))}
      <button type="submit" disabled={loading} className="submit-btn">
        {loading ? "Inferring..." : "Infer Metabolic State"}
      </button>
    </form>
  );
}
