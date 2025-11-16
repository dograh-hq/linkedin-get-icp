/**
 * Custom Use Case Evaluation Page
 * Allows users to define custom evaluation criteria for LinkedIn profile processing
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';

// Type definitions
type Lead = {
  urn: string;
  name: string;
  company_name: string;
  company_website: string;
  email: string;
  title: string;
  profile_url: string;
  icp_fit_strength: string;
  reason: string;
  validation_judgement: string;
  validation_reason: string;
  profile_summary: string;
  company_summary: string;
};

type SkippedProfile = {
  urn: string;
  name: string;
  reason: string;
  profile_url: string;
};

type JobStatus = {
  job_id: string;
  status: 'processing' | 'completed' | 'failed';
  progress: {
    current: number;
    total: number;
    message: string;
  };
  results: Lead[];
  skipped_profiles: SkippedProfile[];
  error?: string;
};

export default function CustomEvaluation() {
  // Track if component has mounted (prevents hydration mismatches)
  const [mounted, setMounted] = useState(false);

  // Input type selection (post vs manual profiles)
  const [inputType, setInputType] = useState<'post' | 'manual'>('post');

  // Post URL input
  const [postUrl, setPostUrl] = useState('');

  // Manual profile URLs input
  const [profileUrls, setProfileUrls] = useState('');

  // Custom criteria fields
  const [useCaseDescription, setUseCaseDescription] = useState('');
  const [targetRoles, setTargetRoles] = useState('');
  const [targetIndustries, setTargetIndustries] = useState('');
  const [companySize, setCompanySize] = useState('');
  const [additionalRequirements, setAdditionalRequirements] = useState('');

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [skippedProfiles, setSkippedProfiles] = useState<SkippedProfile[]>([]);
  const [error, setError] = useState('');

  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Set mounted to true after first render (client-side only)
  useEffect(() => {
    setMounted(true);
  }, []);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  // Poll job status
  const pollJobStatus = async (jid: string) => {
    try {
      const apiKey = sessionStorage.getItem('apiKey');
      const response = await fetch(`/api/job-status/${jid}`, {
        headers: {
          'X-API-Key': apiKey || ''
        }
      });
      if (!response.ok) {
        throw new Error('Failed to fetch job status');
      }

      const data: JobStatus = await response.json();
      setJobStatus(data);

      // Update leads incrementally as results arrive
      if (data.results && data.results.length > 0) {
        setLeads(data.results);
      }

      // Update skipped profiles if any
      if (data.skipped_profiles && data.skipped_profiles.length > 0) {
        setSkippedProfiles(data.skipped_profiles);
      }

      // Stop polling if job completed or failed
      if (data.status === 'completed') {
        setLeads(data.results);
        setSkippedProfiles(data.skipped_profiles || []);
        setIsProcessing(false);
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      } else if (data.status === 'failed') {
        setError(data.error || 'Job failed');
        setIsProcessing(false);
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      }
    } catch (err) {
      console.error('Polling error:', err);
      // Don't stop polling on transient errors, just log them
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsProcessing(true);
    setLeads([]);
    setSkippedProfiles([]);
    setJobStatus(null);
    setJobId(null);

    // Clear any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    try {
      // Get API key from session storage
      const apiKey = sessionStorage.getItem('apiKey');

      // Build custom criteria object (send undefined for empty optional fields, they'll be omitted from JSON)
      const customCriteria: any = {
        use_case_description: useCaseDescription
      };

      // Only include optional fields if they have values
      if (targetRoles && targetRoles.trim()) {
        customCriteria.target_roles = targetRoles.trim();
      }
      if (targetIndustries && targetIndustries.trim()) {
        customCriteria.target_industries = targetIndustries.trim();
      }
      if (companySize && companySize.trim()) {
        customCriteria.company_size = companySize.trim();
      }
      if (additionalRequirements && additionalRequirements.trim()) {
        customCriteria.additional_requirements = additionalRequirements.trim();
      }

      // Choose endpoint based on input type
      const endpoint = inputType === 'post'
        ? '/api/process-post-custom'
        : '/api/process-manual-profiles-custom';

      // Build request body based on input type
      const requestBody = inputType === 'post'
        ? { post_url: postUrl, custom_criteria: customCriteria }
        : {
            profile_urls: profileUrls.split('\n').map(url => url.trim()).filter(url => url),
            custom_criteria: customCriteria
          };

      // Start the job
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey || ''
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error('Failed to start processing');
      }

      const data = await response.json();

      if (data.job_id) {
        setJobId(data.job_id);

        // Start polling every 20 seconds
        pollingIntervalRef.current = setInterval(() => {
          pollJobStatus(data.job_id);
        }, 20000);

        // Poll immediately once
        pollJobStatus(data.job_id);
      } else {
        throw new Error('No job ID returned from server');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setIsProcessing(false);
    }
  };

  // Return null on server-side and first client render to prevent hydration mismatch
  if (!mounted) {
    return null;
  }

  return (
    <div style={{ padding: '40px', maxWidth: '1400px', margin: '0 auto', fontFamily: 'system-ui, sans-serif' }}>
      {/* Navigation */}
      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
        <Link
          href="/"
          style={{
            padding: '8px 16px',
            backgroundColor: '#f5f5f5',
            border: '1px solid #ddd',
            borderRadius: '6px',
            textDecoration: 'none',
            color: '#333',
            fontSize: '14px',
            fontWeight: '500'
          }}
        >
          ← Back to ICP Dashboard
        </Link>
        <div style={{
          padding: '8px 16px',
          backgroundColor: '#0066cc',
          border: '1px solid #0066cc',
          borderRadius: '6px',
          color: 'white',
          fontSize: '14px',
          fontWeight: '600'
        }}>
          Custom Evaluation
        </div>
      </div>

      <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}>
        Custom Use Case Evaluation
      </h1>
      <p style={{ color: '#666', marginBottom: '30px', fontSize: '16px' }}>
        Define your own evaluation criteria to scan LinkedIn profiles
      </p>

      {/* Input Form */}
      <form onSubmit={handleSubmit} style={{ marginBottom: '40px' }}>
        {/* Custom Criteria Fields */}
        <div style={{
          backgroundColor: '#f9f9f9',
          padding: '24px',
          borderRadius: '8px',
          border: '1px solid #ddd',
          marginBottom: '24px'
        }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
            Evaluation Criteria
          </h3>

          {/* Use Case Description - REQUIRED */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontWeight: '500', marginBottom: '6px', fontSize: '14px' }}>
              Use Case Description *
            </label>
            <textarea
              value={useCaseDescription}
              onChange={(e) => setUseCaseDescription(e.target.value)}
              placeholder="Describe what you're looking for. Example: Find potential customers for HR analytics software"
              rows={3}
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '14px',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontFamily: 'system-ui, sans-serif'
              }}
              disabled={isProcessing}
              required
            />
          </div>

          {/* Target Roles - OPTIONAL */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontWeight: '500', marginBottom: '6px', fontSize: '14px' }}>
              Target Job Titles/Roles (optional)
            </label>
            <input
              type="text"
              value={targetRoles}
              onChange={(e) => setTargetRoles(e.target.value)}
              placeholder="Example: HR Director, VP People, CHRO, Head of HR"
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '14px',
                border: '1px solid #ddd',
                borderRadius: '6px'
              }}
              disabled={isProcessing}
            />
          </div>

          {/* Target Industries - OPTIONAL */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontWeight: '500', marginBottom: '6px', fontSize: '14px' }}>
              Target Industries/Sectors (optional)
            </label>
            <input
              type="text"
              value={targetIndustries}
              onChange={(e) => setTargetIndustries(e.target.value)}
              placeholder="Example: SaaS, Fintech, Healthcare, E-commerce"
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '14px',
                border: '1px solid #ddd',
                borderRadius: '6px'
              }}
              disabled={isProcessing}
            />
          </div>

          {/* Company Size - OPTIONAL */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontWeight: '500', marginBottom: '6px', fontSize: '14px' }}>
              Company Size (optional)
            </label>
            <select
              value={companySize}
              onChange={(e) => setCompanySize(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '14px',
                border: '1px solid #ddd',
                borderRadius: '6px',
                backgroundColor: 'white'
              }}
              disabled={isProcessing}
            >
              <option value="">Any</option>
              <option value="1-10 employees">1-10 employees</option>
              <option value="10-50 employees">10-50 employees</option>
              <option value="50-200 employees">50-200 employees</option>
              <option value="200-1000 employees">200-1000 employees</option>
              <option value="1000+ employees">1000+ employees</option>
            </select>
          </div>

          {/* Additional Requirements - OPTIONAL */}
          <div style={{ marginBottom: '0' }}>
            <label style={{ display: 'block', fontWeight: '500', marginBottom: '6px', fontSize: '14px' }}>
              Additional Requirements (optional)
            </label>
            <textarea
              value={additionalRequirements}
              onChange={(e) => setAdditionalRequirements(e.target.value)}
              placeholder="Exclusions, examples, edge cases. Example: Exclude consultants and agencies. Prefer B2B companies with venture funding."
              rows={4}
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '14px',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontFamily: 'system-ui, sans-serif'
              }}
              disabled={isProcessing}
            />
          </div>
        </div>

        {/* Input Type Selection */}
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '12px' }}>
            Profile Source
          </h3>
          <div style={{ display: 'flex', gap: '16px' }}>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="radio"
                value="post"
                checked={inputType === 'post'}
                onChange={(e) => setInputType('post')}
                disabled={isProcessing}
                style={{ marginRight: '8px' }}
              />
              <span style={{ fontSize: '14px', fontWeight: '500' }}>LinkedIn Post URL/ID</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="radio"
                value="manual"
                checked={inputType === 'manual'}
                onChange={(e) => setInputType('manual')}
                disabled={isProcessing}
                style={{ marginRight: '8px' }}
              />
              <span style={{ fontSize: '14px', fontWeight: '500' }}>Manual Profile URLs</span>
            </label>
          </div>
        </div>

        {/* Conditional Input Fields */}
        {inputType === 'post' && (
          <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
            <input
              type="text"
              value={postUrl}
              onChange={(e) => setPostUrl(e.target.value)}
              placeholder="Enter LinkedIn Post URL or ID (e.g., 7392508631268835328)"
              style={{
                flex: 1,
                padding: '12px 16px',
                fontSize: '16px',
                border: '1px solid #ddd',
                borderRadius: '6px'
              }}
              disabled={isProcessing}
              required
            />
          </div>
        )}

        {inputType === 'manual' && (
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontWeight: '500', marginBottom: '6px', fontSize: '14px' }}>
              LinkedIn Profile URLs (one per line)
            </label>
            <textarea
              value={profileUrls}
              onChange={(e) => setProfileUrls(e.target.value)}
              placeholder="https://linkedin.com/in/username1&#10;https://linkedin.com/in/username2&#10;https://linkedin.com/in/username3"
              rows={6}
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '14px',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontFamily: 'system-ui, sans-serif'
              }}
              disabled={isProcessing}
              required
            />
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isProcessing}
          style={{
            padding: '12px 32px',
            fontSize: '16px',
            fontWeight: '600',
            backgroundColor: isProcessing ? '#ccc' : '#0066cc',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: isProcessing ? 'not-allowed' : 'pointer',
            width: '100%'
          }}
        >
          {isProcessing ? 'Processing...' : 'Start Custom Evaluation'}
        </button>
      </form>

      {error && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: '#fee',
          border: '1px solid #fcc',
          borderRadius: '6px',
          color: '#c00',
          marginBottom: '20px'
        }}>
          {error}
        </div>
      )}

      {/* Job ID Display */}
      {jobId && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: '#e7f3ff',
          border: '1px solid #b3d9ff',
          borderRadius: '6px',
          color: '#004085',
          marginBottom: '20px',
          fontSize: '14px'
        }}>
          <strong>Job ID:</strong> {jobId}
        </div>
      )}

      {/* Progress Section */}
      {jobStatus && jobStatus.status === 'processing' && (
        <div style={{
          padding: '20px',
          backgroundColor: '#f5f5f5',
          borderRadius: '8px',
          marginBottom: '30px',
          border: '2px solid #0066cc'
        }}>
          <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '12px', color: '#0066cc' }}>
            ⚙️ Processing in Progress
          </h2>
          <div style={{ marginBottom: '8px' }}>
            <strong>Status:</strong> {jobStatus.progress.message}
          </div>
          <div style={{ marginBottom: '16px' }}>
            <strong>Progress:</strong> {jobStatus.progress.current} / {jobStatus.progress.total} profiles
          </div>

          {/* Progress Bar */}
          <div style={{
            height: '24px',
            backgroundColor: '#ddd',
            borderRadius: '12px',
            overflow: 'hidden',
            position: 'relative'
          }}>
            <div style={{
              height: '100%',
              backgroundColor: '#0066cc',
              width: `${jobStatus.progress.total > 0 ? (jobStatus.progress.current / jobStatus.progress.total) * 100 : 0}%`,
              transition: 'width 0.5s ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontSize: '14px',
              fontWeight: '600'
            }}>
              {jobStatus.progress.total > 0 ?
                `${Math.round((jobStatus.progress.current / jobStatus.progress.total) * 100)}%` :
                '0%'
              }
            </div>
          </div>

          <div style={{ marginTop: '12px', fontSize: '14px', color: '#666' }}>
            ⏱️ This may take a while (~1 minute per profile). Please wait...
          </div>
        </div>
      )}

      {/* Completion Message */}
      {jobStatus && jobStatus.status === 'completed' && (
        <div style={{
          padding: '16px 20px',
          backgroundColor: '#d4edda',
          border: '2px solid #c3e6cb',
          borderRadius: '8px',
          color: '#155724',
          marginBottom: '30px',
          fontSize: '16px',
          fontWeight: '500'
        }}>
          ✅ {jobStatus.progress.message}
        </div>
      )}

      {/* Results Table - Same structure as main page, reuses "ICP Fit" terminology */}
      {leads.length > 0 && (
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '16px' }}>
            Processed Leads ({leads.length})
          </h2>
          <div style={{ overflowX: 'auto' }}>
            <table style={{
              width: '100%',
              borderCollapse: 'collapse',
              backgroundColor: 'white',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              <thead>
                <tr style={{ backgroundColor: '#f9f9f9', borderBottom: '2px solid #ddd' }}>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', width: '150px' }}>Name</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', width: '150px' }}>Company</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', width: '180px' }}>Email</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', width: '120px' }}>Title</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', width: '100px' }}>ICP Fit</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', width: '500px' }}>ICP Reason</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', width: '120px' }}>Validation</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', width: '300px' }}>Validation Reason</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', width: '120px' }}>Profile URL</th>
                </tr>
              </thead>
              <tbody>
                {leads.map((lead, index) => (
                  <tr key={lead.urn || index} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '12px', width: '150px' }}>{lead.name}</td>
                    <td style={{ padding: '12px', width: '150px' }}>
                      <div>{lead.company_name || 'N/A'}</div>
                      {lead.company_website && (
                        <a href={lead.company_website} target="_blank" rel="noopener noreferrer"
                           style={{ color: '#0066cc', fontSize: '12px', textDecoration: 'none', wordBreak: 'break-all' }}>
                          {lead.company_website}
                        </a>
                      )}
                    </td>
                    <td style={{ padding: '12px', width: '180px', fontSize: '13px' }}>{lead.email || 'Not Available'}</td>
                    <td style={{ padding: '12px', width: '120px', fontSize: '13px' }}>{lead.title}</td>
                    <td style={{ padding: '12px', width: '100px' }}>
                      <span style={{
                        padding: '4px 12px',
                        borderRadius: '12px',
                        fontSize: '14px',
                        fontWeight: '500',
                        backgroundColor: lead.icp_fit_strength === 'High' ? '#d4edda' :
                                       lead.icp_fit_strength === 'Medium' ? '#fff3cd' : '#f8d7da',
                        color: lead.icp_fit_strength === 'High' ? '#155724' :
                               lead.icp_fit_strength === 'Medium' ? '#856404' : '#721c24'
                      }}>
                        {lead.icp_fit_strength || 'N/A'}
                      </span>
                    </td>
                    <td style={{ padding: '12px', width: '500px', fontSize: '13px' }}>
                      {lead.reason || 'N/A'}
                    </td>
                    <td style={{ padding: '12px', width: '120px' }}>
                      <span
                        style={{
                          padding: '4px 12px',
                          borderRadius: '12px',
                          fontSize: '14px',
                          fontWeight: '500',
                          backgroundColor: lead.validation_judgement === 'Correct' ? '#d4edda' :
                                         lead.validation_judgement === 'Incorrect' ? '#f8d7da' : '#fff3cd',
                          color: lead.validation_judgement === 'Correct' ? '#155724' :
                                 lead.validation_judgement === 'Incorrect' ? '#721c24' : '#856404'
                        }}
                      >
                        {lead.validation_judgement || 'N/A'}
                      </span>
                    </td>
                    <td style={{ padding: '12px', width: '300px', fontSize: '13px' }}>
                      {lead.validation_reason || 'N/A'}
                    </td>
                    <td style={{ padding: '12px', width: '120px' }}>
                      <a
                        href={lead.profile_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: '#0066cc', textDecoration: 'none', fontWeight: '500', fontSize: '13px', wordBreak: 'break-all' }}
                      >
                        {lead.profile_url}
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Skipped Profiles Section */}
      {skippedProfiles.length > 0 && (
        <div style={{ marginTop: '40px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '16px', color: '#d97706' }}>
            ⚠️ Skipped Profiles ({skippedProfiles.length})
          </h2>
          <div style={{ backgroundColor: '#fff3cd', padding: '16px', borderRadius: '8px', marginBottom: '16px', border: '1px solid #ffc107' }}>
            <strong>Note:</strong> These profiles were skipped due to timeouts ({'>'}180s) or errors during processing.
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{
              width: '100%',
              borderCollapse: 'collapse',
              backgroundColor: 'white',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              <thead>
                <tr style={{ backgroundColor: '#fff3cd', borderBottom: '2px solid #ffc107' }}>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Name</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Skip Reason</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Profile</th>
                </tr>
              </thead>
              <tbody>
                {skippedProfiles.map((profile, index) => (
                  <tr key={profile.urn || index} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '12px' }}>{profile.name || 'Unknown'}</td>
                    <td style={{ padding: '12px', maxWidth: '400px', color: '#d97706' }}>
                      {profile.reason || 'Unknown reason'}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <a
                        href={profile.profile_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: '#0066cc', textDecoration: 'none', fontWeight: '500' }}
                      >
                        View Profile →
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
