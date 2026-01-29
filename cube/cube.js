// Cube.js configuration file
// Note: Most configuration is done via environment variables in docker-compose.yml
module.exports = {
  // Schema path (model files location)
  schemaPath: 'model',

  // Refresh worker configuration
  scheduledRefreshTimer: true,

  // Query rewrite for schema isolation (if needed)
  queryRewrite: (query, { securityContext }) => {
    // Add any query rewriting logic here if needed
    // For example, to enforce row-level security based on tenant
    return query;
  },
};
