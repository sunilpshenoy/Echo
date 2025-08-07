import React from 'react';
import { colors, animation } from '../../styles/designSystem';

const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  onClick,
  className = '',
  type = 'button',
  ...props
}) => {
  const baseClasses = `
    inline-flex items-center justify-center font-medium rounded-xl
    transition-all duration-200 ease-in-out
    focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed
    transform active:scale-[0.98]
  `;

  const variants = {
    primary: `
      bg-gradient-to-r from-primary-500 to-primary-600 
      hover:from-primary-600 hover:to-primary-700 
      text-white shadow-lg hover:shadow-xl
      focus:ring-primary-500 dark:focus:ring-primary-400
      border border-transparent
    `,
    secondary: `
      bg-white dark:bg-slate-800 
      hover:bg-gray-50 dark:hover:bg-slate-700
      text-gray-900 dark:text-gray-100 
      border border-gray-300 dark:border-slate-600
      shadow-sm hover:shadow-md
      focus:ring-gray-500 dark:focus:ring-slate-400
    `,
    outline: `
      bg-transparent hover:bg-primary-50 dark:hover:bg-primary-900/20
      text-primary-600 dark:text-primary-400 
      border border-primary-300 dark:border-primary-600
      hover:border-primary-400 dark:hover:border-primary-500
      focus:ring-primary-500 dark:focus:ring-primary-400
    `,
    ghost: `
      bg-transparent hover:bg-gray-100 dark:hover:bg-slate-700
      text-gray-700 dark:text-gray-300
      border border-transparent
      focus:ring-gray-500 dark:focus:ring-slate-400
    `,
    danger: `
      bg-gradient-to-r from-red-500 to-red-600 
      hover:from-red-600 hover:to-red-700 
      text-white shadow-lg hover:shadow-xl
      focus:ring-red-500 dark:focus:ring-red-400
      border border-transparent
    `,
    success: `
      bg-gradient-to-r from-green-500 to-green-600 
      hover:from-green-600 hover:to-green-700 
      text-white shadow-lg hover:shadow-xl
      focus:ring-green-500 dark:focus:ring-green-400
      border border-transparent
    `
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
    xl: 'px-8 py-4 text-lg'
  };

  const iconSizes = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5', 
    lg: 'h-5 w-5',
    xl: 'h-6 w-6'
  };

  const classes = `
    ${baseClasses}
    ${variants[variant]}
    ${sizes[size]}
    ${fullWidth ? 'w-full' : ''}
    ${className}
  `.trim();

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={classes}
      {...props}
    >
      {loading && (
        <svg className={`animate-spin -ml-1 mr-2 ${iconSizes[size]}`} fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      )}
      
      {icon && iconPosition === 'left' && !loading && (
        <span className={`mr-2 ${iconSizes[size]}`}>
          {icon}
        </span>
      )}
      
      <span>{children}</span>
      
      {icon && iconPosition === 'right' && !loading && (
        <span className={`ml-2 ${iconSizes[size]}`}>
          {icon}
        </span>
      )}
    </button>
  );
};

export default Button;