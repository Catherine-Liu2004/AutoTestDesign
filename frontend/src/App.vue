<template>
  <el-container style="min-height:100vh;background:#f0f2f5">
    <el-header height="56px" style="background:#1e293b;display:flex;align-items:center;padding:0 24px;box-shadow:0 1px 4px rgba(0,0,0,.3)">
      <span style="color:#f1f5f9;font-size:16px;font-weight:600;letter-spacing:.5px;margin-right:32px;white-space:nowrap">
        ⚗️ AutoTestDesign
      </span>
      <el-menu
        mode="horizontal"
        :ellipsis="false"
        background-color="#1e293b"
        text-color="#94a3b8"
        active-text-color="#f1f5f9"
        router
        style="border-bottom:none;flex:1"
      >
        <el-menu-item index="/" style="font-size:14px">
          <el-icon><Upload /></el-icon> Import
        </el-menu-item>
        <el-menu-item index="/requirements" style="font-size:14px">
          <el-icon><List /></el-icon> Requirements
        </el-menu-item>
        <el-menu-item index="/testcases" style="font-size:14px">
          <el-icon><Document /></el-icon> Test Cases
        </el-menu-item>
        <el-menu-item index="/export" style="font-size:14px">
          <el-icon><Download /></el-icon> Export
        </el-menu-item>
      </el-menu>
    </el-header>
    <el-main style="padding:24px;max-width:1400px;margin:0 auto;width:100%">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { Upload, List, Document, Download } from '@element-plus/icons-vue'
</script>

<style>
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
.el-menu--horizontal > .el-menu-item.is-active {
  border-bottom: 2px solid #60a5fa !important;
  color: #f1f5f9 !important;
}
.el-menu--horizontal > .el-menu-item:hover {
  background-color: #334155 !important;
}
.el-card {
  border-radius: 8px !important;
  box-shadow: 0 1px 3px rgba(0,0,0,.08) !important;
}
.el-button--primary { border-radius: 6px !important; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 4px 0; font-size: 20px; color: #1e293b; font-weight: 600; }
.page-header p  { margin: 0; font-size: 13px; color: #64748b; }
</style>
