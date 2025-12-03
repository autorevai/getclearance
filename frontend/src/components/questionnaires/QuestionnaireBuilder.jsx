/**
 * Questionnaire Builder - Simplified
 */

import React, { useState, useEffect } from 'react';
import { Plus, Trash2, AlertCircle } from 'lucide-react';
import { useQuestionnaire, useCreateQuestionnaire, useUpdateQuestionnaire } from '../../hooks/useQuestionnaires';

const styles = {
  form: { display: 'flex', flexDirection: 'column', gap: '16px' },
  row: { display: 'flex', gap: '12px' },
  input: { flex: 1, padding: '8px 12px', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '14px' },
  select: { padding: '8px 12px', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '14px', minWidth: '150px' },
  textarea: { padding: '8px 12px', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '14px', minHeight: '80px', resize: 'vertical' },
  label: { display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '4px' },
  button: { padding: '8px 16px', borderRadius: '6px', border: 'none', cursor: 'pointer', fontSize: '14px', fontWeight: '500' },
  primaryBtn: { backgroundColor: '#3b82f6', color: 'white' },
  secondaryBtn: { backgroundColor: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db' },
  dangerBtn: { backgroundColor: '#fee2e2', color: '#dc2626' },
  question: { padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px', marginBottom: '12px', backgroundColor: '#fafafa' },
  questionHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' },
  checkbox: { display: 'flex', alignItems: 'center', gap: '8px' },
  error: { padding: '12px', backgroundColor: '#fef2f2', borderRadius: '6px', color: '#dc2626', display: 'flex', alignItems: 'center', gap: '8px' },
  actions: { display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '16px' },
};

const QUESTION_TYPES = [
  { value: 'text', label: 'Short Text' },
  { value: 'textarea', label: 'Long Text' },
  { value: 'select', label: 'Single Select' },
  { value: 'multi_select', label: 'Multi Select' },
  { value: 'boolean', label: 'Yes/No' },
  { value: 'number', label: 'Number' },
  { value: 'date', label: 'Date' },
];

export default function QuestionnaireBuilder({ questionnaireId, onClose }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [questionnaireType, setQuestionnaireType] = useState('general');
  const [isActive, setIsActive] = useState(true);
  const [questions, setQuestions] = useState([]);

  const { data: existing, isLoading } = useQuestionnaire(questionnaireId);
  const createMutation = useCreateQuestionnaire();
  const updateMutation = useUpdateQuestionnaire();

  useEffect(() => {
    if (existing) {
      setName(existing.name);
      setDescription(existing.description || '');
      setQuestionnaireType(existing.questionnaire_type);
      setIsActive(existing.is_active);
      setQuestions(existing.questions || []);
    }
  }, [existing]);

  const addQuestion = () => {
    setQuestions([...questions, {
      id: `q_${Date.now()}`,
      type: 'text',
      label: '',
      required: false,
      options: [],
      order: questions.length,
    }]);
  };

  const updateQuestion = (index, field, value) => {
    const updated = [...questions];
    updated[index] = { ...updated[index], [field]: value };
    setQuestions(updated);
  };

  const removeQuestion = (index) => {
    setQuestions(questions.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    const data = { name, description, questionnaire_type: questionnaireType, is_active: isActive, questions };
    try {
      if (questionnaireId) {
        await updateMutation.mutateAsync({ id: questionnaireId, data });
      } else {
        await createMutation.mutateAsync(data);
      }
      onClose();
    } catch (e) {
      console.error(e);
    }
  };

  const error = createMutation.error || updateMutation.error;
  const isSaving = createMutation.isPending || updateMutation.isPending;

  if (isLoading && questionnaireId) {
    return <div>Loading...</div>;
  }

  return (
    <div style={styles.form}>
      {error && (
        <div style={styles.error}>
          <AlertCircle size={16} /> {error.message}
        </div>
      )}

      <div style={styles.row}>
        <div style={{ flex: 1 }}>
          <label style={styles.label}>Name *</label>
          <input style={styles.input} value={name} onChange={(e) => setName(e.target.value)} placeholder="Questionnaire name" />
        </div>
        <div>
          <label style={styles.label}>Type</label>
          <select style={styles.select} value={questionnaireType} onChange={(e) => setQuestionnaireType(e.target.value)}>
            <option value="general">General</option>
            <option value="source_of_funds">Source of Funds</option>
            <option value="pep_declaration">PEP Declaration</option>
            <option value="tax_residency">Tax Residency</option>
          </select>
        </div>
      </div>

      <div>
        <label style={styles.label}>Description</label>
        <textarea style={styles.textarea} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional description..." />
      </div>

      <label style={styles.checkbox}>
        <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
        Active
      </label>

      <h3 style={{ marginTop: '16px', marginBottom: '8px' }}>Questions</h3>

      {questions.map((q, i) => (
        <div key={q.id} style={styles.question}>
          <div style={styles.questionHeader}>
            <strong>Question {i + 1}</strong>
            <button style={{ ...styles.button, ...styles.dangerBtn }} onClick={() => removeQuestion(i)}>
              <Trash2 size={14} />
            </button>
          </div>
          <div style={styles.row}>
            <input
              style={styles.input}
              value={q.label}
              onChange={(e) => updateQuestion(i, 'label', e.target.value)}
              placeholder="Question text"
            />
            <select
              style={styles.select}
              value={q.type}
              onChange={(e) => updateQuestion(i, 'type', e.target.value)}
            >
              {QUESTION_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <label style={{ ...styles.checkbox, marginTop: '8px' }}>
            <input
              type="checkbox"
              checked={q.required}
              onChange={(e) => updateQuestion(i, 'required', e.target.checked)}
            />
            Required
          </label>
          {['select', 'multi_select'].includes(q.type) && (
            <div style={{ marginTop: '8px' }}>
              <label style={styles.label}>Options (comma-separated)</label>
              <input
                style={styles.input}
                value={(q.options || []).join(', ')}
                onChange={(e) => updateQuestion(i, 'options', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                placeholder="Option 1, Option 2, Option 3"
              />
            </div>
          )}
        </div>
      ))}

      <button style={{ ...styles.button, ...styles.secondaryBtn }} onClick={addQuestion}>
        <Plus size={16} /> Add Question
      </button>

      <div style={styles.actions}>
        <button style={{ ...styles.button, ...styles.secondaryBtn }} onClick={onClose}>Cancel</button>
        <button
          style={{ ...styles.button, ...styles.primaryBtn }}
          onClick={handleSubmit}
          disabled={!name || isSaving}
        >
          {isSaving ? 'Saving...' : questionnaireId ? 'Update' : 'Create'}
        </button>
      </div>
    </div>
  );
}
