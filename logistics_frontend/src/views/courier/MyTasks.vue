<template>
  <div class="mobile-container">
    <div class="header">
      <h3>我的派送任务</h3>
      <el-button type="text" @click="loadData">刷新</el-button>
    </div>

    <div v-loading="loading">
      <el-empty v-if="tasks.length === 0" description="今日暂无任务" />
      
      <div v-for="task in tasks" :key="task.tracking_number" class="task-card">
        <div class="card-top">
          <span class="t-no">{{ task.tracking_number }}</span>
          <el-tag size="small">待派送</el-tag>
        </div>
        
        <div class="card-info">
          <div class="row">
            <span class="label">收件人:</span>
            <span class="value">{{ task.receiver_name }}</span>
          </div>
          <div class="row">
            <span class="label">电话:</span>
            <a :href="'tel:'+task.phone" class="phone-link">{{ task.phone }}</a>
          </div>
          <div class="row">
            <span class="label">地址:</span>
            <span class="value address">{{ task.address }}</span>
          </div>
        </div>

        <div class="card-actions">
          <el-button type="danger" plain size="small" @click="handleAction(task, 'fail')">异常反馈</el-button>
          <el-button type="success" size="small" @click="handleAction(task, 'success')">确认签收</el-button>
        </div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="actionType === 'success' ? '签收确认' : '异常上报'" width="90%" center>
      <el-form :model="actionForm">
        <div v-if="actionType === 'success'">
          <el-form-item label="签收人">
            <el-radio-group v-model="actionForm.signer">
              <el-radio label="本人">本人</el-radio>
              <el-radio label="家属">家属</el-radio>
              <el-radio label="驿站">驿站</el-radio>
            </el-radio-group>
          </el-form-item>
        </div>
        <div v-else>
          <el-form-item label="异常原因">
            <el-select v-model="actionForm.fail_reason" style="width: 100%">
              <el-option label="无法联系" value="no_contact" />
              <el-option label="客户拒收" value="rejected" />
              <el-option label="地址错误" value="wrong_address" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitResult">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getCourierTasks, submitDeliveryResult } from '@/api/logistics'
import { ElMessage } from 'element-plus'

const tasks = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const actionType = ref('success') // success | fail
const currentTask = ref(null)

const actionForm = reactive({
  signer: '本人',
  fail_reason: ''
})

const loadData = async () => {
  loading.value = true
  try {
    tasks.value = await getCourierTasks()
  } finally {
    loading.value = false
  }
}

const handleAction = (task, type) => {
  currentTask.value = task
  actionType.value = type
  dialogVisible.value = true
}

const submitResult = async () => {
  const payload = {
    result: actionType.value,
    signer: actionType.value === 'success' ? actionForm.signer : null,
    fail_reason: actionType.value === 'fail' ? actionForm.fail_reason : null,
    geo_location: "39.9042,116.4074" // 实际应调用 navigator.geolocation
  }
  
  try {
    await submitDeliveryResult(currentTask.value.tracking_number, payload)
    ElMessage.success('操作成功')
    dialogVisible.value = false
    loadData() // 刷新列表
  } catch (e) {
    // 错误处理
  }
}

onMounted(() => loadData())
</script>

<style scoped>
/* 简单的移动端样式适配 */
.mobile-container { padding: 10px; background: #f5f7fa; min-height: 100vh; }
.header { display: flex; justify-content: space-between; align-items: center; padding: 0 10px; }
.task-card { background: #fff; border-radius: 8px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05); }
.card-top { display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 10px; }
.t-no { font-weight: bold; font-size: 16px; }
.row { margin-bottom: 8px; display: flex; }
.label { color: #999; width: 60px; flex-shrink: 0; }
.phone-link { color: #409EFF; text-decoration: none; }
.card-actions { text-align: right; margin-top: 10px; border-top: 1px dashed #eee; padding-top: 10px; }
</style>