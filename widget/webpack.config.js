const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const webpack = require('webpack');

module.exports = (env, argv) => {
  const isProduction = argv.mode === 'production';
  
  return {
    entry: './src/index.js',
    output: {
      path: path.resolve(__dirname, 'dist'),
      filename: 'ai-chatbot-widget.js',
      library: 'AIChatbotWidget',
      libraryTarget: 'umd',
      libraryExport: 'default',
      umdNamedDefine: true,
      publicPath: '/'
    },
    module: {
      rules: [
        {
          test: /\.js$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
            options: {
              presets: ['@babel/preset-env', '@babel/preset-react']
            }
          }
        },
        {
          test: /\.css$/,
          use: ['style-loader', 'css-loader']
        }
      ]
    },
    plugins: [
      // Define browser-compatible values for Node.js globals
      new webpack.DefinePlugin({
        'process.env.NODE_ENV': JSON.stringify(argv.mode || 'development'),
        'process.env': '{}',
        'process.platform': JSON.stringify('browser'),
        'process.version': JSON.stringify(''),
      }),
      // Only use HTML plugin for development
      ...(isProduction ? [] : [
        new HtmlWebpackPlugin({
          template: './public/index.html',
          filename: 'index.html'
        })
      ])
    ],
    devServer: {
      static: {
        directory: path.join(__dirname, 'public')
      },
      compress: true,
      port: 9000,
      hot: true,
      historyApiFallback: true
    },
    resolve: {
      extensions: ['.js']
    },
    devtool: isProduction ? 'source-map' : 'eval-source-map'
  };
};