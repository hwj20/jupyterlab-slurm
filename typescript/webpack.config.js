const path = require('path');

module.exports = {
  entry: './src/index.ts',
  mode: 'production',
  module: {
    rules: [
      { test: /\.tsx?$/, use: 'ts-loader', exclude: /node_modules/ },
      { test: /\.svg$/i, type: 'asset/resource' },
      { test: /\.(png|jpe?g|gif)$/i, type: 'asset/resource' }
    ]
  },
  resolve: { extensions: ['.tsx', '.ts', '.js'] },
  output: {
    filename: 'bundle.js',
    path: path.resolve(__dirname, 'lib')
  }
};
