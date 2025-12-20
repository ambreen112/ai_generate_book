import React from 'react';
import OriginalLayout from '@theme-original/Layout';
import RAGChatWidget from '@site/src/components/RAGChatWidget';

export default function Layout(props): JSX.Element {
  return (
    <>
      <OriginalLayout {...props} />
      <RAGChatWidget />
    </>
  );
}