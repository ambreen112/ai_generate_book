import React, { useState } from 'react';
import { useHistory } from '@docusaurus/router';
import useBaseUrl from '@docusaurus/useBaseUrl';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import { useForm } from 'react-hook-form';
import { mockAuthEndpoints } from '../auth/mock-api';

type FormData = {
  email: string;
  password: string;
};

export default function Signin() {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const history = useHistory();
  const baseUrl = useBaseUrl('/');
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>();

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    setError('');

    try {
      // Sign in with mock API
      const result = await mockAuthEndpoints.signIn({
        email: data.email,
        password: data.password,
      });

      if (result.error) {
        throw new Error(result.error?.message || 'Sign in failed');
      }

      // Redirect to home after successful sign in
      console.log('Redirecting to home page...');
      history.push(baseUrl);
    } catch (err: any) {
      setError(err.message || 'An error occurred during sign in');
      console.error('Sign in error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout title="Sign In" description="Sign in to your account for the Physical AI textbook">
      <div className="container margin-vert--lg">
        <div className="row">
          <div className="col col--6 col--offset-3">
            <div className="card">
              <div className="card__header">
                <h2>Sign In</h2>
              </div>
              <div className="card__body">
                {error && <div className="alert alert--danger">{error}</div>}

                <form onSubmit={handleSubmit(onSubmit)}>
                  <div className="margin-bottom--md">
                    <label htmlFor="email">Email</label>
                    <input
                      type="email"
                      id="email"
                      className="form-control"
                      style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                      {...register('email', { required: 'Email is required' })}
                    />
                    {errors.email && <div className="alert alert--warning margin-top--sm">{errors.email.message}</div>}
                  </div>

                  <div className="margin-bottom--md">
                    <label htmlFor="password">Password</label>
                    <input
                      type="password"
                      id="password"
                      className="form-control"
                      style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                      {...register('password', { required: 'Password is required' })}
                    />
                    {errors.password && <div className="alert alert--warning margin-top--sm">{errors.password.message}</div>}
                  </div>

                  <div className="button-group button-group--block">
                    <button type="submit" className="button button--primary" disabled={loading}>
                      {loading ? 'Signing In...' : 'Sign In'}
                    </button>
                  </div>
                </form>
              </div>
              <div className="card__footer">
                <p>
                  Don't have an account? <Link to="/signup">Sign Up</Link>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}