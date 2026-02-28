/**
 * Redux logger middleware — logs dispatched actions in development.
 * Disabled in production to keep the console clean.
 */

const logger = (store) => (next) => (action) => {
  if (process.env.NODE_ENV === 'development') {
    console.group(`[Redux] ${action.type}`);
    console.log('prev state:', store.getState());
    console.log('action:', action);
  }

  const result = next(action);

  if (process.env.NODE_ENV === 'development') {
    console.log('next state:', store.getState());
    console.groupEnd();
  }

  return result;
};

export default logger;
