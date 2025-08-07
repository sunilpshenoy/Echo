import React from 'react';

const Card = ({
  children,
  variant = 'default',
  padding = 'md',
  shadow = 'md',
  hover = false,
  className = '',
  onClick,
  ...props
}) => {
  const baseClasses = `
    bg-white dark:bg-slate-800
    border border-gray-200 dark:border-slate-700
    rounded-xl
    transition-all duration-200 ease-in-out
  `;

  const variants = {
    default: '',
    elevated: 'bg-white dark:bg-slate-800',
    outlined: 'border-2',
    ghost: 'bg-transparent border-transparent shadow-none'
  };

  const paddings = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
    xl: 'p-8'
  };

  const shadows = {
    none: 'shadow-none',
    sm: 'shadow-sm',
    md: 'shadow-md dark:shadow-slate-900/20',
    lg: 'shadow-lg dark:shadow-slate-900/30',
    xl: 'shadow-xl dark:shadow-slate-900/40'
  };

  const hoverEffects = hover ? `
    hover:shadow-lg dark:hover:shadow-slate-900/30 
    hover:-translate-y-0.5 
    cursor-pointer
  ` : '';

  const classes = `
    ${baseClasses}
    ${variants[variant]}
    ${paddings[padding]}
    ${shadows[shadow]}
    ${hoverEffects}
    ${className}
  `.trim();

  return (
    <div
      className={classes}
      onClick={onClick}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;