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
  confirmPassword: string;
  yearsOfExperience: number;
  hardwareKnowledge: boolean;
  favoriteLanguage: string;
};

export default function Signup() {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const history = useHistory();
  const baseUrl = useBaseUrl('/');
  const { register, handleSubmit, formState: { errors }, watch } = useForm<FormData>();

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    setError('');

    try {
      // Create user with mock API
      const result = await mockAuthEndpoints.signUp({
        email: data.email,
        password: data.password,
        profile: {
          yearsOfExperience: data.yearsOfExperience,
          hardwareKnowledge: data.hardwareKnowledge,
          favoriteLanguage: data.favoriteLanguage,
        },
      });

      if (result.error) {
        throw new Error(result.error?.message || 'Sign up failed');
      }

      // Redirect to home after successful signup
      console.log('Redirecting to home page...');
      history.push(baseUrl);
    } catch (err: any) {
      setError(err.message || 'An error occurred during sign up');
      console.error('Sign up error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout title="Sign Up" description="Create an account for the Physical AI textbook">
      <div className="container margin-vert--lg">
        <div className="row">
          <div className="col col--6 col--offset-3">
            <div className="card">
              <div className="card__header">
                <h2>Create an Account</h2>
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
                      {...register('password', {
                        required: 'Password is required',
                        minLength: { value: 6, message: 'Password must be at least 6 characters' }
                      })}
                    />
                    {errors.password && <div className="alert alert--warning margin-top--sm">{errors.password.message}</div>}
                  </div>

                  <div className="margin-bottom--md">
                    <label htmlFor="confirmPassword">Confirm Password</label>
                    <input
                      type="password"
                      id="confirmPassword"
                      className="form-control"
                      style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                      {...register('confirmPassword', {
                        required: 'Please confirm your password',
                        validate: (value) => value === watch('password') || 'Passwords do not match'
                      })}
                    />
                    {errors.confirmPassword && <div className="alert alert--warning margin-top--sm">{errors.confirmPassword.message}</div>}
                  </div>

                  <div className="margin-bottom--md">
                    <label htmlFor="yearsOfExperience">Years of Software Experience</label>
                    <input
                      type="number"
                      id="yearsOfExperience"
                      className="form-control"
                      style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                      {...register('yearsOfExperience', {
                        required: 'Years of experience is required',
                        min: { value: 0, message: 'Years cannot be negative' },
                        max: { value: 50, message: 'Years cannot exceed 50' }
                      })}
                    />
                    {errors.yearsOfExperience && <div className="alert alert--warning margin-top--sm">{errors.yearsOfExperience.message}</div>}
                  </div>

                  <div className="margin-bottom--md">
                    <label>
                      <input
                        type="checkbox"
                        {...register('hardwareKnowledge')}
                      />{' '}
                      Hardware/Robotics Knowledge
                    </label>
                  </div>

                  <div className="margin-bottom--md">
                    <label htmlFor="favoriteLanguage">Favorite Programming Language</label>
                    <input
                      type="text"
                      id="favoriteLanguage"
                      className="form-control"
                      style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                      {...register('favoriteLanguage', { required: 'Favorite language is required' })}
                    />
                    {errors.favoriteLanguage && <div className="alert alert--warning margin-top--sm">{errors.favoriteLanguage.message}</div>}
                  </div>

                  <div className="button-group button-group--block">
                    <button type="submit" className="button button--primary" disabled={loading}>
                      {loading ? 'Creating Account...' : 'Sign Up'}
                    </button>
                  </div>
                </form>
              </div>
              <div className="card__footer">
                <p>
                  Already have an account? <Link to="/signin">Sign In</Link>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}