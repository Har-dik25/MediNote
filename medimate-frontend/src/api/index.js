import { realApi, apiFetch } from './client.js';
import { mockApi } from './mock.js';

const useMocks = String(import.meta.env.VITE_USE_MOCKS).toLowerCase() === 'true';

const hybridApi = {
  ...mockApi, // Base everything on the mock for auth & DB

  // Override AI endpoints to hit the real backend
  generateNote: async (transcript, patientId) => {
    try {
      let region = undefined;
      try {
        const { user } = await mockApi.me();
        region = user.region;
      } catch (e) {}

      const res = await apiFetch('/generate-soap/text', { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript, region }) 
      });
      
      const mockResult = await mockApi.generateNote(transcript, patientId);
      
      // Parse the markdown string returned by the backend into the expected format
      const soapStr = res.soap?.soap_note || '';
      const subjectiveMatch = soapStr.match(/\**Subjective:?\**\s*(.*?)(?=\*\*Objective|\n\s*\**Objective:|$)/is);
      const objectiveMatch = soapStr.match(/\**Objective:?\**\s*(.*?)(?=\*\*Assessment|\n\s*\**Assessment:|$)/is);
      const assessmentMatch = soapStr.match(/\**Assessment:?\**\s*(.*?)(?=\*\*Plan|\n\s*\**Plan:|$)/is);
      const planMatch = soapStr.match(/\**Plan:?\**\s*(.*?)(?=\*\*ICD-10|\n\s*\**ICD-10|\*\*Guidelines|\n\s*\**Guidelines|$)/is);
      
      const parsedSoap = {
        subjective: subjectiveMatch ? subjectiveMatch[1].trim() : (soapStr || ''),
        objective: objectiveMatch ? objectiveMatch[1].trim() : '',
        assessment: assessmentMatch ? assessmentMatch[1].trim() : '',
        plan: planMatch ? planMatch[1].trim() : ''
      };

      await mockApi.saveNote(mockResult.noteId, parsedSoap);
      
      // Map backend ICD-10 format to frontend {code, description}
      const icd10 = (res.icd10 || []).map(item => ({
        code: item.code || '',
        description: item.description || '',
      }));

      // Map backend test format {test, rationale, source} to frontend {code, description}
      const tests = (res.tests || []).map(item => ({
        code: item.code || item.test || '',
        description: item.description || item.rationale || '',
      }));

      return {
        ...mockResult,
        soap: parsedSoap,
        icd10,
        tests,
        safetyFlag: res.soap?.safety?.is_emergency || false,
        safetyReason: res.soap?.safety?.warning || '',
        extractedEntities: res.extracted_entities || null,
      };
    } catch (err) {
      console.error("Real API failed, falling back to mock", err);
      return mockApi.generateNote(transcript, patientId);
    }
  },

  checkDrugInteraction: async (drugA, drugB) => {
    try {
      const res = await apiFetch('/tools/drug-interaction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ drug1: drugA, drug2: drugB })
      });
      return { severity: 'info', message: res.interaction };
    } catch (err) {
      console.error("Real API failed, falling back to mock", err);
      return mockApi.checkDrugInteraction(drugA, drugB);
    }
  },

  searchGuideline: async (query) => {
    try {
      let region = undefined;
      try {
        const { user } = await mockApi.me();
        region = user.region;
      } catch (e) {}

      let url = `/tools/guidelines?query=${encodeURIComponent(query)}`;
      if (region) {
        url += `&region=${encodeURIComponent(region)}`;
      }

      const res = await apiFetch(url);
      return { summary: res.result, source: 'RAG API' };
    } catch (err) {
      console.error("Real API failed, falling back to mock", err);
      return mockApi.searchGuideline(query);
    }
  },

  lookupDrug: async (query) => {
    try {
      const res = await apiFetch(`/tools/drug-info?drug_name=${encodeURIComponent(query)}`);
      return { summary: res.result, drugClass: 'Reference' };
    } catch (err) {
      console.error("Real API failed, falling back to mock", err);
      return mockApi.lookupDrug(query);
    }
  }
};

export const api = useMocks ? hybridApi : realApi;
export { ApiError } from './client.js';
