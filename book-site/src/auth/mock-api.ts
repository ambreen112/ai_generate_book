// Mock API endpoints for Better-Auth in Docusaurus
// This is a client-side mock that simulates the API endpoints
// In a real implementation, you would connect this to an actual backend

class MockAuthAPI {
  private users: any[] = [];
  private sessions: any[] = [];

  constructor() {
    // Load users from localStorage on initialization (only in browser)
    if (typeof window !== 'undefined') {
      this.loadUsersFromStorage();
    }
  }

  private loadUsersFromStorage() {
    if (typeof window === 'undefined') {
      // If not in browser environment, don't attempt to access localStorage
      return;
    }

    const storedUsers = localStorage.getItem('mock-users');
    if (storedUsers) {
      try {
        this.users = JSON.parse(storedUsers);
      } catch (error) {
        console.error('Error parsing stored users:', error);
        this.users = [];
      }
    }
  }

  private saveUsersToStorage() {
    if (typeof window === 'undefined') {
      // If not in browser environment, don't attempt to access localStorage
      return;
    }
    localStorage.setItem('mock-users', JSON.stringify(this.users));
  }

  async signUp(data: any) {
    try {
      // Check if user already exists (now checking persisted data)
      const existingUser = this.users.find(user => user.email === data.email);
      if (existingUser) {
        return {
          error: {
            message: 'User already exists'
          }
        };
      }

      // Create new user
      const newUser = {
        id: Date.now().toString(),
        email: data.email,
        password: data.password, // Store the password for comparison during sign in
        profile: {
          yearsOfExperience: data.profile.yearsOfExperience,
          hardwareKnowledge: data.profile.hardwareKnowledge,
          favoriteLanguage: data.profile.favoriteLanguage,
        },
        createdAt: new Date().toISOString(),
      };

      this.users.push(newUser);
      this.saveUsersToStorage(); // Persist the user data

      // Create a mock session
      const sessionId = `session_${Date.now()}`;
      this.sessions.push({
        id: sessionId,
        userId: newUser.id,
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days
      });

      // Store session in localStorage (only in browser)
      if (typeof window !== 'undefined') {
        localStorage.setItem('mock-session', JSON.stringify({
          user: newUser,
          sessionId,
        }));
      }

      return {
        user: newUser,
        session: {
          id: sessionId,
          userId: newUser.id,
          expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        }
      };
    } catch (error) {
      console.error('Sign up error:', error);
      return {
        error: {
          message: 'An error occurred during sign up'
        }
      };
    }
  }

  async signIn(data: any) {
    try {
      // Find user by email from persisted data
      const user = this.users.find(user => user.email === data.email);
      if (!user) {
        return {
          error: {
            message: 'Invalid email or password'
          }
        };
      }

      // Verify password (since we now store it)
      if (user.password !== data.password) {
        return {
          error: {
            message: 'Invalid email or password'
          }
        };
      }

      // In a real implementation, you would hash and compare passwords properly
      const sessionId = `session_${Date.now()}`;
      this.sessions.push({
        id: sessionId,
        userId: user.id,
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days
      });

      // Store session in localStorage (only in browser)
      if (typeof window !== 'undefined') {
        localStorage.setItem('mock-session', JSON.stringify({
          user,
          sessionId,
        }));
      }

      return {
        user,
        session: {
          id: sessionId,
          userId: user.id,
          expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        }
      };
    } catch (error) {
      console.error('Sign in error:', error);
      return {
        error: {
          message: 'An error occurred during sign in'
        }
      };
    }
  }

  async getCurrentUser() {
    if (typeof window === 'undefined') {
      // If not in browser environment, return null
      return null;
    }

    const sessionData = localStorage.getItem('mock-session');
    if (!sessionData) {
      return null;
    }

    const session = JSON.parse(sessionData);
    return session.user;
  }

  async signOut() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('mock-session');
    }
    return { success: true };
  }
}

// Create a global instance
let mockAuthAPI: MockAuthAPI;

if (typeof window !== 'undefined') {
  mockAuthAPI = new MockAuthAPI();
} else {
  // Create a dummy instance for server-side rendering
  mockAuthAPI = {
    signUp: async () => ({ error: { message: 'Authentication not available during server-side rendering' } }),
    signIn: async () => ({ error: { message: 'Authentication not available during server-side rendering' } }),
    getCurrentUser: async () => null,
    signOut: async () => ({ success: true }),
  } as MockAuthAPI;
}

// Mock API endpoints that can be used by the signup/signin pages
export const mockAuthEndpoints = {
  signUp: async (data: any) => {
    return mockAuthAPI.signUp(data);
  },
  signIn: async (data: any) => {
    return mockAuthAPI.signIn(data);
  },
  getCurrentUser: async () => {
    return mockAuthAPI.getCurrentUser();
  },
  signOut: async () => {
    return mockAuthAPI.signOut();
  },
};

// Export the API instance for direct access
export default mockAuthAPI;