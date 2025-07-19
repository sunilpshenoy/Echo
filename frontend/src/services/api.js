import axios from 'axios';

// API Client with comprehensive error handling and validation
class PulseApiClient {
  constructor(baseURL, token = null) {
    this.baseURL = baseURL;
    this.token = token;
    
    // Create axios instance with interceptors
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor - add auth and validation
    this.client.interceptors.request.use(
      (config) => {
        // Add authentication token
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }

        // Log request for debugging
        console.log('🚀 API Request:', {
          method: config.method?.toUpperCase(),
          url: config.url,
          data: config.data
        });

        return config;
      },
      (error) => {
        console.error('❌ Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor - handle errors and validation
    this.client.interceptors.response.use(
      (response) => {
        // Log successful response
        console.log('✅ API Response:', {
          status: response.status,
          url: response.config.url,
          data: response.data
        });

        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Handle network errors
        if (!error.response) {
          console.error('🔌 Network Error:', error.message);
          throw new Error('Network connection failed. Please check your internet connection.');
        }

        // Handle specific HTTP status codes
        switch (error.response.status) {
          case 400:
            console.error('🚫 Bad Request:', error.response.data);
            throw new Error(error.response.data?.detail || 'Invalid request data');

          case 401:
            console.error('🔒 Unauthorized:', error.response.data);
            // Try token refresh if not already attempted
            if (!originalRequest._retry && this.token) {
              originalRequest._retry = true;
              try {
                await this.refreshToken();
                originalRequest.headers.Authorization = `Bearer ${this.token}`;
                return this.client(originalRequest);
              } catch (refreshError) {
                // Refresh failed, redirect to login
                this.handleLogout();
                throw new Error('Session expired. Please log in again.');
              }
            } else {
              this.handleLogout();
              throw new Error('Authentication failed. Please log in again.');
            }

          case 403:
            console.error('⛔ Forbidden:', error.response.data);
            throw new Error('You do not have permission to perform this action.');

          case 404:
            console.error('🔍 Not Found:', error.response.data);
            throw new Error('The requested resource was not found.');

          case 422:
            console.error('📝 Validation Error:', error.response.data);
            const validationErrors = error.response.data?.detail;
            if (Array.isArray(validationErrors)) {
              const errorMessages = validationErrors.map(err => 
                `${err.loc?.join?.('.') || 'Field'}: ${err.msg}`
              ).join(', ');
              throw new Error(`Validation errors: ${errorMessages}`);
            }
            throw new Error(error.response.data?.detail || 'Invalid data provided');

          case 429:
            console.error('⏰ Rate Limited:', error.response.data);
            throw new Error('Too many requests. Please wait a moment and try again.');

          case 500:
            console.error('💥 Server Error:', error.response.data);
            throw new Error('Server error occurred. Please try again later.');

          case 502:
          case 503:
          case 504:
            console.error('🚧 Service Unavailable:', error.response.data);
            throw new Error('Service is temporarily unavailable. Please try again later.');

          default:
            console.error('❓ Unknown Error:', error.response);
            throw new Error(`An error occurred (${error.response.status}). Please try again.`);
        }
      }
    );
  }

  // Update token
  setToken(token) {
    this.token = token;
  }

  // Remove token
  clearToken() {
    this.token = null;
  }

  // Token refresh method
  async refreshToken() {
    try {
      const response = await this.client.post('/auth/refresh');
      if (response.data.access_token) {
        this.setToken(response.data.access_token);
        localStorage.setItem('token', response.data.access_token);
        return response.data.access_token;
      }
      throw new Error('No access token received');
    } catch (error) {
      console.error('Token refresh failed:', error);
      throw error;
    }
  }

  // Handle logout
  handleLogout() {
    this.clearToken();
    localStorage.removeItem('token');
    // Trigger app logout - this could be improved with a callback
    window.location.href = '/';
  }

  // Validate data against expected schema
  validateApiResponse(data, expectedFields = []) {
    if (!data || typeof data !== 'object') {
      throw new Error('Invalid API response format');
    }

    const missingFields = expectedFields.filter(field => 
      data[field] === undefined || data[field] === null
    );

    if (missingFields.length > 0) {
      throw new Error(`API response missing required fields: ${missingFields.join(', ')}`);
    }

    return true;
  }

  // Common API methods with validation

  // Authentication methods
  async login(email, password) {
    const response = await this.client.post('/login', { email, password });
    this.validateApiResponse(response.data, ['access_token', 'user']);
    return response.data;
  }

  async register(userData) {
    const response = await this.client.post('/register', userData);
    this.validateApiResponse(response.data, ['user']);
    return response.data;
  }

  // User methods
  async getUser() {
    const response = await this.client.get('/users/me');
    this.validateApiResponse(response.data, ['user_id', 'email']);
    return response.data;
  }

  // Marketplace methods
  async createListing(listingData) {
    // Validate required fields before sending
    const requiredFields = ['title', 'description', 'category'];
    const missingFields = requiredFields.filter(field => !listingData[field]);
    
    if (missingFields.length > 0) {
      throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
    }

    // Validate category against known values
    const validCategories = ['items', 'services', 'jobs', 'housing', 'vehicles'];
    if (!validCategories.includes(listingData.category)) {
      throw new Error(`Invalid category. Must be one of: ${validCategories.join(', ')}`);
    }

    const response = await this.client.post('/marketplace/listings', listingData);
    this.validateApiResponse(response.data, ['listing_id']);
    return response.data;
  }

  async getListings(filters = {}) {
    const response = await this.client.get('/marketplace/listings', { params: filters });
    this.validateApiResponse(response.data, ['listings']);
    return response.data;
  }

  // Teams/Groups methods
  async createTeam(teamData) {
    const requiredFields = ['name'];
    const missingFields = requiredFields.filter(field => !teamData[field]);
    
    if (missingFields.length > 0) {
      throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
    }

    const response = await this.client.post('/teams', teamData);
    this.validateApiResponse(response.data, ['team_id', 'name']);
    return response.data;
  }

  async getTeams() {
    const response = await this.client.get('/teams');
    this.validateApiResponse(response.data, ['teams']);
    return response.data;
  }

  // Generic methods
  async get(endpoint, params = {}) {
    const response = await this.client.get(endpoint, { params });
    return response.data;
  }

  async post(endpoint, data = {}) {
    const response = await this.client.post(endpoint, data);
    return response.data;
  }

  async put(endpoint, data = {}) {
    const response = await this.client.put(endpoint, data);
    return response.data;
  }

  async delete(endpoint) {
    const response = await this.client.delete(endpoint);
    return response.data;
  }
}

export default PulseApiClient;