import React from 'react';

interface CardProps {
  id?: string;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  badge?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  id,
  title,
  subtitle,
  badge,
  className = '',
  children,
}) => {
  return (
    <section id={id} className={`card ${className}`}>
      {(title || subtitle || badge) && (
        <div className="card-header">
          <div className="card-title-group">
            {title && <h2 className="card-title">{title}</h2>}
            {subtitle && <p className="card-subtitle">{subtitle}</p>}
          </div>
          {badge && <div className="card-badge-slot">{badge}</div>}
        </div>
      )}
      <div className="card-body">{children}</div>
    </section>
  );
};
