<template>
  <el-card class="box-card" header="📦 新运单录入">
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-divider content-position="left">发件方</el-divider>
          <el-form-item label="姓名" prop="sender.name">
            <el-input v-model="form.sender.name" placeholder="发件人姓名" />
          </el-form-item>
          <el-form-item label="电话" prop="sender.phone">
            <el-input v-model="form.sender.phone" placeholder="联系电话" />
          </el-form-item>
          <el-form-item label="地址" prop="sender.address">
            <el-input v-model="form.sender.address" type="textarea" :rows="2" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-divider content-position="left">收件方</el-divider>
          <el-form-item label="姓名" prop="receiver.name">
            <el-input v-model="form.receiver.name" placeholder="收件人姓名" />
          </el-form-item>
          <el-form-item label="电话" prop="receiver.phone">
            <el-input v-model="form.receiver.phone" placeholder="联系电话" />
          </el-form-item>
          <el-form-item label="地址" prop="receiver.address">
            <el-input v-model="form.receiver.address" type="textarea" :rows="2" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">包裹规格</el-divider>
      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="重量 (kg)" prop="weight">
            <el-input-number v-model="form.weight" :precision="2" :step="0.1" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="体积" prop="volume">
            <el-input v-model="form.volume" placeholder="长x宽x高 (cm)" />
          </el-form-item>
        </el-col>
      </el-row>

      <div style="text-align: center; margin-top: 20px;">
        <el-button type="primary" @click="submitForm(formRef)" size="large" :loading="loading">
          立即下单
        </el-button>
        <el-button @click="resetForm(formRef)">重置</el-button>
      </div>
    </el-form>

    <el-dialog v-model="dialogVisible" title="✅ 下单成功" width="30%">
      <div style="text-align: center; line-height: 2;">
        <h3>运单号: <span style="color: #409EFF">{{ resultData.tracking_number }}</span></h3>
        <p>下一站: <strong>{{ resultData.next_station }}</strong></p>
        <p style="color: #909399; font-size: 12px;">系统已自动规划路由</p>
      </div>
      <template #footer>
        <el-button type="primary" @click="dialogVisible = false">打印面单</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { createParcel } from '@/api/logistics'
import { ElMessage } from 'element-plus'

const formRef = ref(null)
const loading = ref(false)
const dialogVisible = ref(false)
const resultData = ref({})

const form = reactive({
  sender: { name: '', phone: '', address: '' },
  receiver: { name: '', phone: '', address: '' },
  weight: 1.0,
  volume: '',
  start_station_id: 1 // 模拟：通常从当前登录用户的Store中获取
})

const rules = {
  'sender.name': [{ required: true, message: '请输入发件人', trigger: 'blur' }],
  'receiver.name': [{ required: true, message: '请输入收件人', trigger: 'blur' }],
  weight: [{ required: true, message: '请输入重量', trigger: 'blur' }]
}

const submitForm = async (formEl) => {
  if (!formEl) return
  await formEl.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const res = await createParcel(form)
        resultData.value = res
        dialogVisible.value = true
        // 清空表单
        formEl.resetFields()
      } catch (error) {
        // 错误已由 request.js 统一处理
      } finally {
        loading.value = false
      }
    }
  })
}

const resetForm = (formEl) => {
  if (!formEl) return
  formEl.resetFields()
}
</script>