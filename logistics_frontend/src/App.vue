<template>
  <div class="app-layout">
    <el-container>
      <el-header>
        <el-menu
          :default-active="activeIndex"
          mode="horizontal"
          router
          background-color="#545c64"
          text-color="#fff"
          active-text-color="#ffd04b"
        >
          <el-menu-item index="/login">Login</el-menu-item>
          <el-menu-item index="/create-parcel">Create Parcel</el-menu-item>
          <el-menu-item index="/trace-parcel">Trace Parcel</el-menu-item>
          <el-menu-item index="/transport-task">Transport Task</el-menu-item>
          <el-menu-item index="/delivery-task">Last Mile Delivery</el-menu-item>
        </el-menu>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeIndex = ref('/login')

watch(
  () => route.path,
  (newPath) => {
    activeIndex.value = newPath
  }
)
</script>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
.app-layout {
  min-height: 100vh;
}
.el-header {
  padding: 0;
}
</style>
