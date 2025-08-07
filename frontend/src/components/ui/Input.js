import React, { forwardRef } from 'react';

const Input = forwardRef(({
  type = 'text',
  variant = 'default',
  size = 'md',
  error = false,
  disabled = false,
  fullWidth = false,
  icon,
  iconPosition = 'left',
  className = '',
  label,
  helperText,
  errorText,
  placeholder,
  ...props
}, ref) => {
  const baseClasses = `
    border rounded-lg transition-all duration-200 ease-in-out
    focus:outline-none focus:ring-2 focus:border-transparent
    disabled:opacity-50 disabled:cursor-not-allowed
    bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100
  `;

  const variants = {
    default: `
      border-gray-300 dark:border-slate-600
      hover:border-gray-400 dark:hover:border-slate-500
      focus:ring-primary-500 focus:ring-opacity-50
    `,
    outline: `
      border-2 border-gray-300 dark:border-slate-600
      hover:border-primary-400 dark:hover:border-primary-500
      focus:ring-primary-500 focus:ring-opacity-50
    `,
    filled: `
      bg-gray-100 dark:bg-slate-600 border-transparent
      hover:bg-gray-200 dark:hover:bg-slate-500
      focus:ring-primary-500 focus:ring-opacity-50
    `
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-4 py-3 text-base'
  };

  const errorStyles = error ? `
    border-red-500 dark:border-red-400
    focus:ring-red-500 focus:ring-opacity-50
    text-red-900 dark:text-red-100
    bg-red-50 dark:bg-red-900/10
  ` : '';

  const iconSize = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-5 w-5'
  };

  const iconSpacing = {
    sm: iconPosition === 'left' ? 'pl-9' : 'pr-9',
    md: iconPosition === 'left' ? 'pl-10' : 'pr-10',
    lg: iconPosition === 'left' ? 'pl-12' : 'pr-12'
  };

  const inputClasses = `
    ${baseClasses}
    ${variants[variant]}
    ${sizes[size]}
    ${errorStyles}
    ${icon ? iconSpacing[size] : ''}
    ${fullWidth ? 'w-full' : ''}
    ${className}
  `.trim();

  return (
    <div className={fullWidth ? 'w-full' : ''}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {label}
        </label>
      )}
      
      <div className="relative">
        {icon && iconPosition === 'left' && (
          <div className={`absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500 ${iconSize[size]}`}>
            {icon}
          </div>
        )}
        
        <input
          ref={ref}
          type={type}
          disabled={disabled}
          placeholder={placeholder}
          className={inputClasses}
          {...props}
        />
        
        {icon && iconPosition === 'right' && (
          <div className={`absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500 ${iconSize[size]}`}>
            {icon}
          </div>
        )}
      </div>
      
      {(helperText || errorText) && (
        <p className={`mt-1 text-xs ${
          error 
            ? 'text-red-600 dark:text-red-400' 
            : 'text-gray-500 dark:text-gray-400'
        }`}>
          {error ? errorText : helperText}
        </p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;