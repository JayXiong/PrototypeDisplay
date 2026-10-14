<template>
  <div>
    <div class="toolbar">
      <el-input
        v-model="search"
        placeholder="搜索项目名称"
        clearable
        style="width: 240px"
        @input="load"
      />
      <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 120px" @change="load">
        <el-option label="启用" :value="1" />
        <el-option label="禁用" :value="0" />
      </el-select>
      <div style="flex: 1"></div>
      <el-button type="primary" @click="openDialog()">+ 新建项目</el-button>
    </div>

    <el-table :data="projects" v-loading="loading" stripe>
      <el-table-column prop="name" label="项目名称" min-width="140" />
      <el-table-column prop="remark" label="备注" min-width="160" show-overflow-tooltip>
        <template #default="{ row }">{{ row.remark || '-' }}</template>
      </el-table-column>
      <el-table-column label="访问链接" min-width="220">
        <template #default="{ row }">
          <el-link type="primary" :href="`/p/${row.slug}/`" target="_blank" :disabled="row.status !== 1">
            {{ origin }}/p/{{ row.slug }}/
          </el-link>
        </template>
      </el-table-column>
      <el-table-column prop="visits" label="总访问" width="90" align="center" />
      <el-table-column prop="today_visits" label="今日" width="80" align="center" />
      <el-table-column prop="updated_at" label="更新时间" width="180" />
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-switch
            :model-value="row.status === 1"
            :disabled="row._statusLoading"
            @change="(v) => toggleStatus(row, v)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" align="center">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
          <el-popconfirm title="确定删除该项目？文件与统计将一并删除" width="240" @confirm="del(row)">
            <template #reference>
              <el-button link type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑项目' : '新建项目'" width="480px">
      <el-form label-width="90px">
        <el-form-item label="项目名称" required>
          <el-input v-model="form.name" placeholder="例如：XX 系统首页原型" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="选填" />
        </el-form-item>
        <el-form-item :label="editing ? '替换原型' : '原型文件'" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".html,.zip"
            :on-change="onFileChange"
            :on-remove="() => (form.file = null)"
            drag
          >
            <div style="padding: 12px 0">拖拽文件到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持单个 .html 文件或包含 index.html 的 .zip 包，最大 50MB</div>
            </template>
          </el-upload>
          <div v-if="editing" style="color: #909399; font-size: 12px">
            留空则不替换原型文件，仅更新名称和备注
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api, { errMsg } from '../api'

const origin = location.origin
const projects = ref([])
const loading = ref(false)
const search = ref('')
const statusFilter = ref(null)
const dialogVisible = ref(false)
const saving = ref(false)
const editing = ref(null)
const uploadRef = ref()
const form = reactive({ name: '', remark: '', file: null })

async function load() {
  loading.value = true
  try {
    const params = {}
    if (search.value) params.search = search.value
    if (statusFilter.value !== null && statusFilter.value !== '') params.status = statusFilter.value
    const { data } = await api.get('/projects', { params })
    projects.value = data.map((p) => ({ ...p, _statusLoading: false }))
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    loading.value = false
  }
}

function onFileChange(file) {
  form.file = file.raw
}

function openDialog(row) {
  editing.value = row || null
  form.name = row?.name || ''
  form.remark = row?.remark || ''
  form.file = null
  uploadRef.value?.clearFiles()
  dialogVisible.value = true
}

async function save() {
  if (!editing.value && !form.file) {
    ElMessage.warning('请上传原型文件')
    return
  }
  if (!form.name.trim()) {
    ElMessage.warning('请填写项目名称')
    return
  }
  saving.value = true
  try {
    const fd = new FormData()
    fd.append('name', form.name)
    fd.append('remark', form.remark)
    if (form.file) fd.append('file', form.file)
    if (editing.value) {
      await api.put(`/projects/${editing.value.id}`, fd)
      ElMessage.success('项目已更新')
    } else {
      await api.post('/projects', fd)
      ElMessage.success('项目已创建')
    }
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    saving.value = false
  }
}

async function toggleStatus(row, enabled) {
  row._statusLoading = true
  try {
    await api.put(`/projects/${row.id}/status?status=${enabled ? 1 : 0}`)
    row.status = enabled ? 1 : 0
    ElMessage.success(enabled ? '已启用' : '已禁用')
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    row._statusLoading = false
  }
}

async function del(row) {
  try {
    await api.delete(`/projects/${row.id}`)
    ElMessage.success('已删除')
    load()
  } catch (e) {
    ElMessage.error(errMsg(e))
  }
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; align-items: center; }
</style>
