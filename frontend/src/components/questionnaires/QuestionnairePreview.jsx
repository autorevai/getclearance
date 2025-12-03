/**
 * Questionnaire Preview - Simplified
 */

import React from 'react';
import { AlertCircle } from 'lucide-react';
import { useQuestionnaire } from '../../hooks/useQuestionnaires';

const styles = {
  container: { display: 'flex', flexDirection: 'column', gap: '16px' },
  header: { padding: '16px', backgroundColor: '#f9fafb', borderRadius: '8px', border: '1px solid #e5e7eb' },
  badge: { display: 'inline-block', padding: '2px 8px', borderRadius: '12px', fontSize: '12px', fontWeight: '500', marginLeft: '8px' },
  question: { padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px' },
  questionLabel: { fontWeight: '500', marginBottom: '4px' },
  meta: { display: 'flex', gap: '16px', marginTop: '12px', fontSize: '13px', color: '#6b7280' },
  options: { marginTop: '8px', paddingLeft: '16px' },
  option: { padding: '4px 0', fontSize: '14px' },
  error: { padding: '16px', backgroundColor: '#fef2f2', borderRadius: '8px', color: '#dc2626' },
  loader: { padding: '32px', textAlign: 'center', color: '#6b7280' },
};

export default function QuestionnairePreview({ questionnaireId }) {
  const { data: q, isLoading, error } = useQuestionnaire(questionnaireId);

  if (isLoading) return <div style={styles.loader}>Loading...</div>;
  if (error) return <div style={styles.error}><AlertCircle size={16} /> {error.message}</div>;
  if (!q) return <div style={styles.error}>Questionnaire not found</div>;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <h3 style={{ margin: 0 }}>{q.name}</h3>
          <span style={{ ...styles.badge, backgroundColor: q.is_active ? '#dcfce7' : '#f3f4f6', color: q.is_active ? '#16a34a' : '#6b7280' }}>
            {q.is_active ? 'Active' : 'Inactive'}
          </span>
        </div>
        {q.description && <p style={{ margin: '8px 0 0', color: '#6b7280', fontSize: '14px' }}>{q.description}</p>}
        <div style={styles.meta}>
          <span>Type: {q.questionnaire_type.replace(/_/g, ' ')}</span>
          <span>Questions: {q.question_count}</span>
          <span>Version: {q.version}</span>
        </div>
      </div>

      {(q.questions || []).map((question, i) => (
        <div key={question.id || i} style={styles.question}>
          <div style={styles.questionLabel}>
            {i + 1}. {question.label}
            {question.required && <span style={{ color: '#dc2626' }}> *</span>}
          </div>
          <div style={{ fontSize: '13px', color: '#6b7280' }}>
            Type: {question.type.replace(/_/g, ' ')}
          </div>
          {question.options?.length > 0 && (
            <div style={styles.options}>
              {question.options.map((opt, j) => (
                <div key={j} style={styles.option}>• {opt}</div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
