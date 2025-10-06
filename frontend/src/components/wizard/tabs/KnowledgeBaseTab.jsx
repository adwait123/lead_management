import React, { useState } from 'react';
import { useHatchWizard } from '../HatchWizardContext';
import { Card, CardHeader, CardTitle, CardContent } from '../../ui/Card';
import { Button } from '../../ui/Button';

export function KnowledgeBaseTab() {
  const { wizardData, updateWizardData } = useHatchWizard();
  const [businessProfile, setBusinessProfile] = useState(wizardData.businessProfile || {});
  const [faqItems, setFaqItems] = useState(wizardData.faq || []);
  const [newFaqQuestion, setNewFaqQuestion] = useState('');
  const [newFaqAnswer, setNewFaqAnswer] = useState('');

  // Essential business fields only
  const profileFields = [
    { key: 'company_name', label: 'Company Name', type: 'text', placeholder: 'Acme Home Services' },
    { key: 'service_area', label: 'Service Area', type: 'text', placeholder: 'Dallas, TX and surrounding areas' },
    { key: 'phone_number', label: 'Phone Number', type: 'tel', placeholder: '(555) 123-4567' },
    { key: 'hours', label: 'Business Hours', type: 'text', placeholder: 'Monday-Friday 8AM-6PM' },
    { key: 'services_offered', label: 'Main Services', type: 'textarea', placeholder: 'Plumbing, HVAC, electrical services' }
  ];

  // Quick FAQ suggestions
  const suggestedFaqs = [
    { question: 'Do you offer emergency services?', answer: 'Yes, we provide 24/7 emergency services for urgent issues.' },
    { question: 'What forms of payment do you accept?', answer: 'We accept cash, check, and all major credit cards.' },
    { question: 'Do you provide free estimates?', answer: 'Yes, we provide free estimates for all jobs.' },
    { question: 'Are you licensed and insured?', answer: 'Yes, we are fully licensed and insured.' }
  ];

  const handleProfileChange = (key, value) => {
    const updatedProfile = { ...businessProfile, [key]: value };
    setBusinessProfile(updatedProfile);
    updateWizardData({ businessProfile: updatedProfile });
  };

  const addFaqItem = () => {
    if (newFaqQuestion.trim() && newFaqAnswer.trim()) {
      const newFaq = [...faqItems, { question: newFaqQuestion.trim(), answer: newFaqAnswer.trim() }];
      setFaqItems(newFaq);
      updateWizardData({ faq: newFaq });
      setNewFaqQuestion('');
      setNewFaqAnswer('');
    }
  };

  const addSuggestedFaq = (faq) => {
    const newFaq = [...faqItems, faq];
    setFaqItems(newFaq);
    updateWizardData({ faq: newFaq });
  };

  const removeFaqItem = (index) => {
    const newFaq = faqItems.filter((_, i) => i !== index);
    setFaqItems(newFaq);
    updateWizardData({ faq: newFaq });
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Knowledge Base
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Add business information and FAQs that your agent can reference when helping customers.
        </p>
      </div>

      {/* Business Profile */}
      <Card className="border-0 shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            Business Information
            <span className="text-sm font-normal text-gray-500 ml-2">(Optional but recommended)</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {profileFields.map((field) => (
              <div key={field.key} className={field.type === 'textarea' ? 'md:col-span-2' : ''}>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {field.label}
                </label>
                {field.type === 'textarea' ? (
                  <textarea
                    value={businessProfile[field.key] || ''}
                    onChange={(e) => handleProfileChange(field.key, e.target.value)}
                    placeholder={field.placeholder}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  />
                ) : (
                  <input
                    type={field.type}
                    value={businessProfile[field.key] || ''}
                    onChange={(e) => handleProfileChange(field.key, e.target.value)}
                    placeholder={field.placeholder}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  />
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* FAQ Section */}
      <Card className="border-0 shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center">
            <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center mr-3">
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            Frequently Asked Questions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600 mb-6">
            Add common questions customers ask. Your agent will use these to provide quick, accurate answers.
          </p>

          {/* Quick Add Suggestions */}
          {suggestedFaqs.filter(suggested =>
            !faqItems.some(existing => existing.question === suggested.question)
          ).length > 0 && (
            <div className="mb-6">
              <h4 className="font-medium text-gray-900 mb-3">Quick Add - Common Questions</h4>
              <div className="grid grid-cols-1 gap-3">
                {suggestedFaqs.filter(suggested =>
                  !faqItems.some(existing => existing.question === suggested.question)
                ).map((faq, index) => (
                  <div key={index} className="flex items-center justify-between bg-gray-50 border rounded-lg p-3">
                    <div className="flex-1">
                      <h5 className="font-medium text-gray-900 text-sm">{faq.question}</h5>
                      <p className="text-gray-600 text-xs mt-1">{faq.answer}</p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => addSuggestedFaq(faq)}
                      className="ml-4 text-green-600 hover:text-green-700 hover:bg-green-50 border-green-200"
                    >
                      Add
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Current FAQ Items */}
          {faqItems.length > 0 && (
            <div className="space-y-3 mb-6">
              <h4 className="font-medium text-gray-900">Your FAQ Items ({faqItems.length})</h4>
              {faqItems.map((faq, index) => (
                <div key={index} className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h5 className="font-medium text-gray-900 mb-2">{faq.question}</h5>
                      <p className="text-gray-600 text-sm">{faq.answer}</p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => removeFaqItem(index)}
                      className="ml-4 text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                    >
                      Remove
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Add New FAQ */}
          <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-6">
            <h4 className="font-medium text-gray-900 mb-4">Add Custom FAQ</h4>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Question</label>
                <input
                  type="text"
                  value={newFaqQuestion}
                  onChange={(e) => setNewFaqQuestion(e.target.value)}
                  placeholder="What question do customers often ask?"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Answer</label>
                <textarea
                  value={newFaqAnswer}
                  onChange={(e) => setNewFaqAnswer(e.target.value)}
                  placeholder="How should your agent respond to this question?"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              <Button
                onClick={addFaqItem}
                disabled={!newFaqQuestion.trim() || !newFaqAnswer.trim()}
                className="bg-purple-600 hover:bg-purple-700"
              >
                Add FAQ Item
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary */}
      <div className="bg-gray-50 rounded-lg p-4 text-center">
        <div className="text-sm text-gray-600">
          <strong>{Object.keys(businessProfile).filter(key => businessProfile[key]).length}</strong> business fields completed
          {faqItems.length > 0 && (
            <span className="ml-4">
              <strong>{faqItems.length}</strong> FAQ items added
            </span>
          )}
        </div>
      </div>
    </div>
  );
}