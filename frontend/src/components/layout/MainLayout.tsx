import React from 'react';
import { Header } from './Header';
import { PageContainer } from './PageContainer';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <PageContainer>
      <Header />
      <main 
        style={{
          flex: 1,
          width: '100%',
          maxWidth: '1920px',
          margin: '0 auto',
          overflow: 'hidden',
        }}
      >
        {children}
      </main>
    </PageContainer>
  );
};
