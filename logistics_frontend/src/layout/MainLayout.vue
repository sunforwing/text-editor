<template>
  <div class="common-layout">
    <el-container>
      <el-aside width="200px" class="aside-menu">
        <div class="logo">📦 物流系统</div>
        <el-menu
          active-text-color="#ffd04b"
          background-color="#545c64"
          class="el-menu-vertical-demo"
          default-active="/station/entry"
          text-color="#fff"
          router
        >
          <el-menu-item index="/station/entry">
            <el-icon><Edit /></el-icon>
            <span>运单录入</span>
          </el-menu-item>
          
          <el-menu-item index="/tracking">
            <el-icon><Search /></el-icon>
            <span>轨迹查询</span>
          </el-menu-item>

          <el-menu-item index="/courier/tasks">
            <el-icon><Van /></el-icon>
            <span>(切换到手机端)</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <el-header class="header-bar">
          <span>物流管理控制台 (Phase 1)</span>
          <el-button type="info" size="small">退出</el-button>
        </el-header>
        
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { Edit, Search, Van } from '@element-plus/icons-vue'
// 注意：图标需要单独引入，如果没显示图标也没关系，不影响功能
</script>

<style scoped>
.common-layout { height: 100vh; display: flex; }
.el-container { height: 100%; }
.aside-menu { background-color: #545c64; color: white; }
.logo { height: 60px; line-height: 60px; text-align: center; font-size: 18px; font-weight: bold; background: #434a50; }
.header-bar { background-color: #fff; border-bottom: 1px solid #ddd; line-height: 60px; display: flex; justify-content: space-between; align-items: center; }
.el-main { background-color: #f0f2f5; padding: 20px; }
</style>