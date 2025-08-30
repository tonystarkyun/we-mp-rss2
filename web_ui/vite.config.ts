import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig(({ command, mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    // 定义全局 feature flags
    define: {
      __VUE_OPTIONS_API__: true,
      __VUE_PROD_DEVTOOLS__: false,
      __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false
    },
    // 基础路径配置
    base: command === "serve" ? "/" : "/",
    // 开发服务器配置
    // 构建配置
    build: {
      outDir: "../static",
      emptyOutDir: true,
      assetsDir: "assets",
    },
    server: {
      host: "0.0.0.0",
      port: 3000,
      proxy: {
        "/static": {
          target: env.VITE_API_BASE_URL,
          changeOrigin: true,
        },
        "/files": {
          target: env.VITE_API_BASE_URL,
          changeOrigin: true,
        },
        "/rss": {
          target: env.VITE_API_BASE_URL,
          changeOrigin: true,
        },
        "/feed": {
          target: env.VITE_API_BASE_URL,
          changeOrigin: true,
        },
        "/api": {
          target: env.VITE_API_BASE_URL,
          changeOrigin: true,
        },
      },
    },
  };
});