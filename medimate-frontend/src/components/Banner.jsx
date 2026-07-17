import { motion } from 'framer-motion';

export default function Banner({ variant = 'info', title, children, icon }) {
  return (
    <motion.div
      className={`banner banner--${variant}`}
      role={variant === 'danger' ? 'alert' : 'status'}
      initial={{ opacity: 0, y: -8, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
    >
      <span className="banner__icon" aria-hidden="true">{icon ?? <DefaultIcon variant={variant} />}</span>
      <div>
        {title && <p className="banner__title">{title}</p>}
        <p className="banner__text">{children}</p>
      </div>
    </motion.div>
  );
}

function DefaultIcon({ variant }) {
  if (variant === 'danger') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
        <path d="M12 9v4M12 17h.01M10.3 3.9L2.7 17a2 2 0 0 0 1.7 3h15.2a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
      <path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
    </svg>
  );
}
