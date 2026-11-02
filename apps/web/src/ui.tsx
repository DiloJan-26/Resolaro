import type { ButtonHTMLAttributes, PropsWithChildren } from 'react';

export function Button({ children, secondary, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { secondary?: boolean }) {
  return <button className={secondary ? 'button button-secondary' : 'button'} {...props}>{children}</button>;
}
export function Card({ children }: PropsWithChildren) { return <section className="card">{children}</section>; }
export function Notice({ children, error = false }: PropsWithChildren<{ error?: boolean }>) { return <div className="notice" role={error ? 'alert' : 'status'}>{children}</div>; }
