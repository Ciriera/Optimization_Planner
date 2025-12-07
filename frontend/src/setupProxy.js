const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
    app.use(
        '/api',
        createProxyMiddleware({
            target: 'http://localhost:8000',
            changeOrigin: true,
            secure: false,
            logLevel: 'debug',
            onProxyReq: (proxyReq, req, res) => {
                console.log(`[Proxy] ${req.method} ${req.url} -> http://localhost:8000${req.url}`);
            },
            onError: (err, req, res) => {
                console.error('[Proxy Error]', err);
                res.status(500).json({
                    error: 'Proxy error',
                    message: err.message
                });
            }
        })
    );
};

