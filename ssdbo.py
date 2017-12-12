"""
date: 2017/11/10
author: lslcode [jasonli8848@qq.com]
"""

import numpy as np
import tensorflow as tf

class SSDBO:
    def __init__(self, tf_sess, isTraining):
        # tensorflow session
        self.sess = tf_sess
        # 是否训练
        self.isTraining = isTraining
        # 允许的图像大小
        self.img_size = [300, 300]
        # 分类总数量
        self.classes_size = 21
        # 背景分类的值
        self.background_classes_val = 0
        # 每个特征图单元的default box数量
        self.default_box_size = [4, 6, 6, 6, 4, 4]
        # default box 尺寸长宽比例
        self.box_aspect_ratio = [
            [1.0, 1.25, 2.0, 3.0],
            [1.0, 1.25, 2.0, 3.0, 1.0 / 2.0, 1.0 / 3.0],
            [1.0, 1.25, 2.0, 3.0, 1.0 / 2.0, 1.0 / 3.0],
            [1.0, 1.25, 2.0, 3.0, 1.0 / 2.0, 1.0 / 3.0],
            [1.0, 1.25, 2.0, 3.0],
            [1.0, 1.25, 2.0, 3.0]
        ]
        # 最小default box面积比例
        self.min_box_scale = 0.2
        # 最大default box面积比例
        self.max_box_scale = 0.9
        # 每个特征层的面积比例
        # numpy生成等差数组，效果等同于论文中的s_k=s_min+(s_max-s_min)*(k-1)/(m-1)
        self.default_box_scale = np.linspace(self.min_box_scale, self.max_box_scale, num = np.amax(self.default_box_size))
        print('##   default_box_scale:'+str(self.default_box_scale))
        # 卷积步长
        self.conv_strides_1 = [1, 1, 1, 1]
        self.conv_strides_2 = [1, 2, 2, 1]
        self.conv_strides_3 = [1, 3, 3, 1]
        # 池化窗口
        self.pool_size = [1, 2, 2, 1]
        # 池化步长
        self.pool_strides = [1, 2, 2, 1]
        # Batch Normalization 算法的 decay 参数
        self.conv_bn_decay = 0.999
        # Batch Normalization 算法的 variance_epsilon 参数
        self.conv_bn_epsilon = 0.0001
        # Jaccard相似度判断阀值
        self.jaccard_value = 0.5

        # 初始化Tensorflow Graph
        self.generate_graph()
        
    def generate_graph(self):

        # 输入数据
        self.input = tf.placeholder(shape=[None, self.img_size[0], self.img_size[1], 3], dtype=tf.float32, name='input_image')
        self.dropout_keep_prob = tf.placeholder(tf.float32) 
 
        # vvg16卷积层 1 相关参数权重
        self.conv_weight_1_1 = tf.Variable(tf.truncated_normal([3, 3,  3, 64], 0, 1), dtype=tf.float32, name='weight_1_1')
        self.conv_weight_1_2 = tf.Variable(tf.truncated_normal([3, 3, 64, 64], 0, 1), dtype=tf.float32, name='weight_1_2')
        self.conv_bias_1_1 = tf.Variable(tf.truncated_normal([64], 0, 1), dtype=tf.float32, name='bias_1_1')
        self.conv_bias_1_2 = tf.Variable(tf.truncated_normal([64], 0, 1), dtype=tf.float32, name='bias_1_2')        
    
        # vvg16卷积层 2 相关参数权重
        self.conv_weight_2_1 = tf.Variable(tf.truncated_normal([3, 3,  64, 128], 0, 1), dtype=tf.float32, name='weight_2_1')
        self.conv_weight_2_2 = tf.Variable(tf.truncated_normal([3, 3, 128, 128], 0, 1), dtype=tf.float32, name='weight_2_2')
        self.conv_bias_2_1 = tf.Variable(tf.truncated_normal([128], 0, 1), dtype=tf.float32, name='bias_2_1')
        self.conv_bias_2_2 = tf.Variable(tf.truncated_normal([128], 0, 1), dtype=tf.float32, name='bias_2_2')        
    
        # vvg16卷积层 3 相关参数权重
        self.conv_weight_3_1 = tf.Variable(tf.truncated_normal([3, 3, 128, 256], 0, 1), dtype=tf.float32, name='weight_3_1')
        self.conv_weight_3_2 = tf.Variable(tf.truncated_normal([3, 3, 256, 256], 0, 1), dtype=tf.float32, name='weight_3_2')
        self.conv_bias_3_1 = tf.Variable(tf.truncated_normal([256], 0, 1), dtype=tf.float32, name='bias_3_1')
        self.conv_bias_3_2 = tf.Variable(tf.truncated_normal([256], 0, 1), dtype=tf.float32, name='bias_3_2')
    
        # vvg16卷积层 4 相关参数权重
        self.conv_weight_4_1 = tf.Variable(tf.truncated_normal([3, 3, 256, 512], 0, 1), dtype=tf.float32, name='weight_4_1')
        self.conv_weight_4_2 = tf.Variable(tf.truncated_normal([3, 3, 512, 512], 0, 1), dtype=tf.float32, name='weight_4_2')
        self.conv_bias_4_1 = tf.Variable(tf.truncated_normal([512], 0, 1), dtype=tf.float32, name='bias_4_1')
        self.conv_bias_4_2 = tf.Variable(tf.truncated_normal([512], 0, 1), dtype=tf.float32, name='bias_4_2')   
    
        # vvg16卷积层 5 相关参数权重
        self.conv_weight_5_1 = tf.Variable(tf.truncated_normal([3, 3, 512, 512], 0, 1), dtype=tf.float32, name='weight_5_1')
        self.conv_weight_5_2 = tf.Variable(tf.truncated_normal([3, 3, 512, 512], 0, 1), dtype=tf.float32, name='weight_5_2')
        self.conv_bias_5_1 = tf.Variable(tf.truncated_normal([512], 0, 1), dtype=tf.float32, name='bias_5_1')
        self.conv_bias_5_2 = tf.Variable(tf.truncated_normal([512], 0, 1), dtype=tf.float32, name='bias_5_2')
    
        # 卷积层 6 相关参数权重
        self.conv_weight_6_1 = tf.Variable(tf.truncated_normal([3, 3, 512, 1024], 0, 1), dtype=tf.float32, name='weight_6_1')
        self.conv_bias_6_1 = tf.Variable(tf.truncated_normal([1024], 0, 1), dtype=tf.float32, name='bias_6_1')        
    
        # 卷积层 7 相关参数权重
        self.conv_weight_7_1 = tf.Variable(tf.truncated_normal([1, 1, 1024, 1024], 0, 1), dtype=tf.float32, name='weight_7_1')
        self.conv_bias_7_1 = tf.Variable(tf.truncated_normal([1024], 0, 1), dtype=tf.float32, name='bias_7_1')        
    
        # 卷积层 8 相关参数权重
        self.conv_weight_8_1 = tf.Variable(tf.truncated_normal([1, 1, 1024, 256], 0, 1), dtype=tf.float32, name='weight_8_1')
        self.conv_weight_8_2 = tf.Variable(tf.truncated_normal([3, 3,  256, 512], 0, 1), dtype=tf.float32, name='weight_8_2')
        self.conv_bias_8_1 = tf.Variable(tf.truncated_normal([256], 0, 1), dtype=tf.float32, name='bias_8_1')
        self.conv_bias_8_2 = tf.Variable(tf.truncated_normal([512], 0, 1), dtype=tf.float32, name='bias_8_2')        
    
        # 卷积层 9 相关参数权重
        self.conv_weight_9_1 = tf.Variable(tf.truncated_normal([1, 1, 512, 128], 0, 1), dtype=tf.float32, name='weight_9_1')
        self.conv_weight_9_2 = tf.Variable(tf.truncated_normal([3, 3, 128, 256], 0, 1), dtype=tf.float32, name='weight_9_2')
        self.conv_bias_9_1 = tf.Variable(tf.truncated_normal([128], 0, 1), dtype=tf.float32, name='bias_9_1')
        self.conv_bias_9_2 = tf.Variable(tf.truncated_normal([256], 0, 1), dtype=tf.float32, name='bias_9_2')        
    
        # 卷积层 10 相关参数权重
        self.conv_weight_10_1 = tf.Variable(tf.truncated_normal([1, 1, 256, 128], 0, 1), dtype=tf.float32, name='weight_10_1')
        self.conv_weight_10_2 = tf.Variable(tf.truncated_normal([3, 3, 128, 256], 0, 1), dtype=tf.float32, name='weight_10_2')
        self.conv_bias_10_1 = tf.Variable(tf.truncated_normal([128], 0, 1), dtype=tf.float32, name='bias_10_1')
        self.conv_bias_10_2 = tf.Variable(tf.truncated_normal([256], 0, 1), dtype=tf.float32, name='bias_10_2')

        # ssd卷积特征层 相关参数权重
        self.features_weight_1 = tf.Variable(tf.truncated_normal([3, 3, 512,  self.default_box_size[0] * self.classes_size], 0, 1), name='features_weight_1')
        self.features_bias_1 = tf.Variable(tf.truncated_normal([self.default_box_size[0] * self.classes_size], 0, 1), name='features_bias_1')
        self.features_weight_2 = tf.Variable(tf.truncated_normal([3, 3, 1024, self.default_box_size[1] * self.classes_size], 0, 1), name='features_weight_2')
        self.features_bias_2 = tf.Variable(tf.truncated_normal([self.default_box_size[1] * self.classes_size], 0, 1), name='features_bias_2')
        self.features_weight_3 = tf.Variable(tf.truncated_normal([3, 3, 512,  self.default_box_size[2] * self.classes_size], 0, 1), name='features_weight_3')
        self.features_bias_3 = tf.Variable(tf.truncated_normal([self.default_box_size[2] * self.classes_size], 0, 1), name='features_bias_3')
        self.features_weight_4 = tf.Variable(tf.truncated_normal([3, 3, 256,  self.default_box_size[3] * self.classes_size], 0, 1), name='features_weight_4')
        self.features_bias_4 = tf.Variable(tf.truncated_normal([self.default_box_size[3] * self.classes_size], 0, 1), name='features_bias_4')
        self.features_weight_5 = tf.Variable(tf.truncated_normal([3, 3, 256,  self.default_box_size[4] * self.classes_size], 0, 1), name='features_weight_5')
        self.features_bias_5 = tf.Variable(tf.truncated_normal([self.default_box_size[4] * self.classes_size], 0, 1), name='features_bias_5')
        self.features_weight_6 = tf.Variable(tf.truncated_normal([1, 1, 256,  self.default_box_size[5] * self.classes_size], 0, 1), name='features_weight_6')
        self.features_bias_6 = tf.Variable(tf.truncated_normal([self.default_box_size[5] * self.classes_size], 0, 1), name='features_bias_6')
    
        # vvg16卷积层 1
        self.conv_1_1 = tf.nn.conv2d(self.input, self.conv_weight_1_1, self.conv_strides_1, padding='SAME', name='conv_1_1')
        self.conv_1_1 = self.batch_normalization(self.conv_1_1)
        self.conv_1_1 = tf.nn.relu(tf.add(self.conv_1_1, self.conv_bias_1_1), name='relu_1_1')
        self.conv_1_2 = tf.nn.conv2d(self.conv_1_1, self.conv_weight_1_2, self.conv_strides_1, padding='SAME', name='conv_1_2')
        self.conv_1_2 = self.batch_normalization(self.conv_1_2)
        self.conv_1_2 = tf.nn.relu(tf.add(self.conv_1_2, self.conv_bias_1_2), name='relu_1_2')
        self.conv_1_2 = tf.nn.max_pool(self.conv_1_2, self.pool_size, self.pool_strides, padding='SAME', name='pool_1_2')
        print('##   conv_1_2 shape: ' + str(self.conv_1_2.get_shape().as_list()))
        # vvg16卷积层 2
        self.conv_2_1 = tf.nn.conv2d(self.conv_1_2, self.conv_weight_2_1, self.conv_strides_1, padding='SAME', name='conv_2_1')
        self.conv_2_1 = self.batch_normalization(self.conv_2_1)
        self.conv_2_1 = tf.nn.relu(tf.add(self.conv_2_1, self.conv_bias_2_1), name='relu_2_1')
        self.conv_2_2 = tf.nn.conv2d(self.conv_2_1, self.conv_weight_2_2, self.conv_strides_1, padding='SAME', name='conv_2_2')
        self.conv_2_2 = self.batch_normalization(self.conv_2_2)
        self.conv_2_2 = tf.nn.relu(tf.add(self.conv_2_2, self.conv_bias_2_2), name='relu_2_2')
        self.conv_2_2 = tf.nn.max_pool(self.conv_2_2, self.pool_size, self.pool_strides, padding='SAME',   name='pool_2_2')
        print('##   conv_2_2 shape: ' + str(self.conv_2_2.get_shape().as_list()))
        # vvg16卷积层 3
        self.conv_3_1 = tf.nn.conv2d(self.conv_2_2, self.conv_weight_3_1, self.conv_strides_1, padding='SAME', name='conv_3_1')
        self.conv_3_1 = self.batch_normalization(self.conv_3_1)
        self.conv_3_1 = tf.nn.relu(tf.add(self.conv_3_1, self.conv_bias_3_1), name='relu_3_1')
        self.conv_3_2 = tf.nn.conv2d(self.conv_3_1, self.conv_weight_3_2, self.conv_strides_1, padding='SAME', name='conv_3_2')
        self.conv_3_2 = self.batch_normalization(self.conv_3_2)
        self.conv_3_2 = tf.nn.relu(tf.add(self.conv_3_2, self.conv_bias_3_2), name='relu_3_2')
        self.conv_3_2 = tf.nn.max_pool(self.conv_3_2, self.pool_size, self.pool_strides, padding='SAME', name='pool_3_3')
        print('##   conv_3_2 shape: ' + str(self.conv_3_2.get_shape().as_list()))
        # vvg16卷积层 4
        self.conv_4_1 = tf.nn.conv2d(self.conv_3_2, self.conv_weight_4_1, self.conv_strides_1, padding='SAME', name='conv_4_1')
        self.conv_4_1 = self.batch_normalization(self.conv_4_1)
        self.conv_4_1 = tf.nn.relu(tf.add(self.conv_4_1, self.conv_bias_4_1), name='relu_4_1')
        self.conv_4_2 = tf.nn.conv2d(self.conv_4_1, self.conv_weight_4_2, self.conv_strides_1, padding='SAME', name='conv_4_2')
        self.conv_4_2 = self.batch_normalization(self.conv_4_2)
        self.conv_4_2 = tf.nn.relu(tf.add(self.conv_4_2, self.conv_bias_4_2), name='relu_4_2')
        #self.conv_4_2 = tf.nn.max_pool(self.conv_4_2, self.pool_size, self.pool_strides, padding='SAME',   name='pool_4_3')
        print('##   conv_4_2 shape: ' + str(self.conv_4_2.get_shape().as_list()))
        # vvg16卷积层 5
        self.conv_5_1 = tf.nn.conv2d(self.conv_4_2, self.conv_weight_5_1, self.conv_strides_1, padding='SAME', name='conv_5_1')
        self.conv_5_1 = self.batch_normalization(self.conv_5_1)
        self.conv_5_1 = tf.nn.relu(tf.add(self.conv_5_1, self.conv_bias_5_1), name='relu_5_1')
        self.conv_5_2 = tf.nn.conv2d(self.conv_5_1, self.conv_weight_5_2, self.conv_strides_1, padding='SAME', name='conv_5_2')
        self.conv_5_2 = self.batch_normalization(self.conv_5_2)
        self.conv_5_2 = tf.nn.relu(tf.add(self.conv_5_2, self.conv_bias_5_2), name='relu_5_2')
        self.conv_5_2 = tf.nn.max_pool(self.conv_5_2, self.pool_size, self.pool_strides, padding='SAME',   name='pool_5_3')
        print('##   conv_5_2 shape: ' + str(self.conv_5_2.get_shape().as_list()))
        # ssd卷积层 6
        self.conv_6_1 = tf.nn.conv2d(self.conv_5_2, self.conv_weight_6_1, self.conv_strides_1, padding='SAME', name='conv_6_1')
        self.conv_6_1 = self.batch_normalization(self.conv_6_1)
        self.conv_6_1 = tf.nn.relu(tf.add(self.conv_6_1, self.conv_bias_6_1), name='relu_6_1')
        #self.conv_6_1 = tf.nn.dropout(self.conv_6_1, self.dropout_keep_prob) 
        print('##   conv_6_1 shape: ' + str(self.conv_6_1.get_shape().as_list()))
        # ssd卷积层 7
        self.conv_7_1 = tf.nn.conv2d(self.conv_6_1, self.conv_weight_7_1, self.conv_strides_1, padding='SAME', name='conv_7_1')
        self.conv_7_1 = self.batch_normalization(self.conv_7_1)
        self.conv_7_1 = tf.nn.relu(tf.add(self.conv_7_1, self.conv_bias_7_1), name='relu_7_1')
        #self.conv_7_1 = tf.nn.dropout(self.conv_7_1, self.dropout_keep_prob) 
        print('##   conv_7_1 shape: ' + str(self.conv_7_1.get_shape().as_list()))
        # ssd卷积层 8
        self.conv_8_1 = tf.nn.conv2d(self.conv_7_1, self.conv_weight_8_1, self.conv_strides_1, padding='SAME', name='conv_8_1')
        self.conv_8_1 = self.batch_normalization(self.conv_8_1)
        self.conv_8_1 = tf.nn.relu(tf.add(self.conv_8_1, self.conv_bias_8_1), name='relu_8_1')
        self.conv_8_2 = tf.nn.conv2d(self.conv_8_1, self.conv_weight_8_2, self.conv_strides_2, padding='SAME', name='conv_8_2')
        self.conv_8_2 = self.batch_normalization(self.conv_8_2)
        self.conv_8_2 = tf.nn.relu(tf.add(self.conv_8_2, self.conv_bias_8_2), name='relu_8_2')
        print('##   conv_8_2 shape: ' + str(self.conv_8_2.get_shape().as_list()))
        # ssd卷积层 9
        self.conv_9_1 = tf.nn.conv2d(self.conv_8_2, self.conv_weight_9_1, self.conv_strides_1, padding='SAME', name='conv_9_1')
        self.conv_9_1 = self.batch_normalization(self.conv_9_1)
        self.conv_9_1 = tf.nn.relu(tf.add(self.conv_9_1, self.conv_bias_9_1), name='relu_9_1')
        self.conv_9_2 = tf.nn.conv2d(self.conv_9_1, self.conv_weight_9_2, self.conv_strides_2, padding='SAME', name='conv_9_2')
        self.conv_9_2 = self.batch_normalization(self.conv_9_2)
        self.conv_9_2 = tf.nn.relu(tf.add(self.conv_9_2, self.conv_bias_9_2), name='relu_9_2')
        print('##   conv_9_2 shape: ' + str(self.conv_9_2.get_shape().as_list()))
        # ssd卷积层 10
        self.conv_10_1 = tf.nn.conv2d(self.conv_9_2, self.conv_weight_10_1, self.conv_strides_1, padding='SAME', name='conv_10_1')
        self.conv_10_1 = self.batch_normalization(self.conv_10_1)
        self.conv_10_1 = tf.nn.relu(tf.add(self.conv_10_1, self.conv_bias_10_1), name='relu_10_1')
        self.conv_10_2 = tf.nn.conv2d(self.conv_10_1, self.conv_weight_10_2, self.conv_strides_2, padding='SAME', name='conv_10_2')
        self.conv_10_2 = self.batch_normalization(self.conv_10_2)
        self.conv_10_2 = tf.nn.relu(tf.add(self.conv_10_2, self.conv_bias_10_2), name='relu_10_2')
        print('##   conv_10_2 shape: ' + str(self.conv_10_2.get_shape().as_list()))
        # ssd卷积层 11
        self.conv_11 = tf.nn.avg_pool(self.conv_10_2, self.pool_size, self.pool_strides, "VALID")
        print('##   conv_11 shape: ' + str(self.conv_11.get_shape().as_list()))

        # 第 1 层 特征层，来源于conv_4_2
        self.features_1 = tf.nn.conv2d(self.conv_4_2, self.features_weight_1, self.conv_strides_1, padding='SAME', name='conv_features_1')
        self.features_1 = self.batch_normalization(self.features_1)
        self.features_1 = tf.nn.relu(tf.add(self.features_1, self.features_bias_1),name='relu_features_1')
        print('##   features_1 shape: ' + str(self.features_1.get_shape().as_list()))
        # 第 2 层 特征层，来源于conv_7_1
        self.features_2 = tf.nn.conv2d(self.conv_7_1, self.features_weight_2, self.conv_strides_1, padding='SAME', name='conv_features_2')
        self.features_2 = self.batch_normalization(self.features_2)
        self.features_2 = tf.nn.relu(tf.add(self.features_2, self.features_bias_2),name='relu_features_2')
        print('##   features_2 shape: ' + str(self.features_2.get_shape().as_list()))
        # 第 3 层 特征层，来源于conv_8_2
        self.features_3 = tf.nn.conv2d(self.conv_8_2, self.features_weight_3, self.conv_strides_1, padding='SAME', name='conv_features_3')
        self.features_3 = self.batch_normalization(self.features_3)
        self.features_3 = tf.nn.relu(tf.add(self.features_3, self.features_bias_3),name='relu_features_3')
        print('##   features_3 shape: ' + str(self.features_3.get_shape().as_list()))
        # 第 4 层 特征层，来源于conv_9_2
        self.features_4 = tf.nn.conv2d(self.conv_9_2, self.features_weight_4, self.conv_strides_1, padding='SAME', name='conv_features_4')
        self.features_4 = self.batch_normalization(self.features_4)
        self.features_4 = tf.nn.relu(tf.add(self.features_4, self.features_bias_4),name='relu_features_4')
        print('##   features_4 shape: ' + str(self.features_4.get_shape().as_list()))
        # 第 5 层 特征层，来源于conv_10_2
        self.features_5 = tf.nn.conv2d(self.conv_10_2,self.features_weight_5, self.conv_strides_1, padding='SAME', name='conv_features_5')
        self.features_5 = self.batch_normalization(self.features_5)
        self.features_5 = tf.nn.relu(tf.add(self.features_5, self.features_bias_5),name='relu_features_5')
        print('##   features_5 shape: ' + str(self.features_5.get_shape().as_list()))
        # 第 6 层 特征层，来源于conv_11
        self.features_6 = tf.nn.conv2d(self.conv_11,self.features_weight_6, self.conv_strides_1, padding='SAME', name='conv_features_6')  
        self.features_6 = self.batch_normalization(self.features_6)
        self.features_6 = tf.nn.relu(tf.add(self.features_6, self.features_bias_6),name='relu_features_6')
        print('##   features_6 shape: ' + str(self.features_6.get_shape().as_list()))
        
        # 特征层集合
        self.feature_maps = [self.features_1, self.features_2, self.features_3, self.features_4, self.features_5, self.features_6]
        # 获取卷积后各个特征层的shape,以便生成feature和groundtruth格式一致的训练数据
        self.feature_maps_shape = [m.get_shape().as_list() for m in self.feature_maps]
        
        # 整理feature数据
        self.feature_class = []
        for i, fmap in zip(range(len(self.feature_maps)), self.feature_maps):
            width = self.feature_maps_shape[i][1]
            height = self.feature_maps_shape[i][2]
            self.feature_class.append(tf.reshape(fmap, [-1, (width * height * self.default_box_size[i]) , self.classes_size]))
        # 合并每张图像产生的所有特征
        self.feature_class = tf.concat(self.feature_class, axis=1)
        print('##   feature_class shape : ' + str(self.feature_class.get_shape().as_list()))

        # 生成所有default boxs
        self.all_default_boxs = self.generate_all_default_boxs()
        self.all_default_boxs_len = len(self.all_default_boxs)
        print('##   all default boxs : ' + str(self.all_default_boxs_len))

        # 输入真实数据
        self.groundtruth_class = tf.placeholder(shape=[None,self.all_default_boxs_len], dtype=tf.int32,name='groundtruth_class')
        self.groundtruth_positives = tf.placeholder(shape=[None,self.all_default_boxs_len], dtype=tf.float32,name='groundtruth_positives')
        self.groundtruth_positives_weight = tf.placeholder(shape=[None,self.all_default_boxs_len], dtype=tf.float32,name='groundtruth_positives_weight')
        self.groundtruth_negatives = tf.placeholder(shape=[None,self.all_default_boxs_len], dtype=tf.float32,name='groundtruth_negatives')

        # 损失函数
        self.groundtruth_count = tf.add(self.groundtruth_positives, self.groundtruth_negatives)
        self.groundtruth_count_weight = tf.add(tf.multiply(self.groundtruth_positives, self.groundtruth_positives_weight), self.groundtruth_negatives)
        self.loss_all = tf.reduce_sum((tf.nn.sparse_softmax_cross_entropy_with_logits(logits=self.feature_class, labels=self.groundtruth_class) * self.groundtruth_count_weight), reduction_indices=1) / tf.reduce_sum(self.groundtruth_count, reduction_indices = 1)
        
        # loss优化函数
        self.optimizer = tf.train.AdamOptimizer(0.0001)
        #self.optimizer = tf.train.GradientDescentOptimizer(0.001)
        self.train = self.optimizer.minimize(self.loss_all)

    # 图像检测与训练
    # input_images : 输入图像数据，格式:[None,width,hight,channel]
    # actual_data : 标注数据，格式:[None,[None,top_X,top_Y,width,hight,classes]] , classes值范围[0,classes_size)
    def run(self, input_images, actual_data):
        # 训练部分
        if self.isTraining :
            if actual_data is None :
                raise Exception('actual_data参数不存在!')
            if len(input_images) != len(actual_data):
                raise Exception('input_images 与 actual_data参数长度不对应!')

            f_class = self.sess.run(self.feature_class, feed_dict={self.input : input_images, self.dropout_keep_prob : 0.5})

            #检查数据是否正确
            f_class = self.check_numerics(f_class,'预测集f_class')
               
            with tf.control_dependencies([self.feature_class]):
                gt_class,gt_positives,gt_positives_weight,gt_negatives = self.generate_groundtruth_data(actual_data, f_class)
                #print('gt_positives :【'+str(np.sum(gt_positives))+'|'+str(np.amax(gt_positives))+'|'+str(np.amin(gt_positives))+'】|gt_positives_weight :【'+str(np.sum(gt_positives_weight))+'|'+str(np.amax(gt_positives_weight))+'|'+str(np.amin(gt_positives_weight))+'】|gt_negatives : 【'+str(np.sum(gt_negatives))+'|'+str(np.amax(gt_negatives))+'|'+str(np.amin(gt_negatives))+'】')
                self.sess.run(self.train, feed_dict={
                    self.input : input_images,
                    self.dropout_keep_prob : 0.5,
                    self.groundtruth_class : gt_class,
                    self.groundtruth_positives : gt_positives,
                    self.groundtruth_positives_weight : gt_positives_weight,
                    self.groundtruth_negatives : gt_negatives
                })
                loss_all = self.sess.run(self.loss_all, feed_dict={
                    self.input : input_images,
                    self.dropout_keep_prob : 0.5,
                    self.groundtruth_class : gt_class,
                    self.groundtruth_positives : gt_positives,
                    self.groundtruth_positives_weight : gt_positives_weight,
                    self.groundtruth_negatives : gt_negatives
                })
                #检查数据是否正确
                loss_all = self.check_numerics(loss_all,'损失值loss_all') 
                return loss_all, f_class 
        # 检测部分
        else :
            # softmax归一化预测结果
            feature_class_softmax = tf.nn.softmax(logits=self.feature_class, dim=-1)
            # 过滤background的预测值
            background_filter = np.ones(self.classes_size, dtype=np.float32)
            background_filter[self.background_classes_val] = 0 
            background_filter = tf.constant(background_filter)  
            feature_class_softmax=tf.multiply(feature_class_softmax, background_filter)
            # 计算每个box的最大预测值
            feature_class_softmax = tf.reduce_max(feature_class_softmax,2)
            # 过滤冗余的预测结果
            box_top_set = tf.nn.top_k(feature_class_softmax, 300)
            box_top_index = box_top_set.indices
            box_top_value = box_top_set.values
            f_class, f_class_softmax, box_top_index, box_top_value = self.sess.run(
                [self.feature_class, feature_class_softmax, box_top_index, box_top_value], 
                feed_dict={
                    self.input : input_images, 
                    self.dropout_keep_prob : 1
                }
            )
            #检查数据是否正确
            f_class = self.check_numerics(f_class,'预测集f_class')
            box_top_index = self.check_numerics(box_top_index,'预测集box_top_index')
            box_top_value = self.check_numerics(box_top_value,'预测集box_top_value')

            top_shape = np.shape(box_top_index)
            pred_class = []
            pred_class_val = []
            pred_location = []
            for i in range(top_shape[0]) :
                item_img_class = []
                item_img_class_val = []
                item_img_location = []
                for j in range(top_shape[1]) : 
                    p_class_val = f_class_softmax[i][box_top_index[i][j]]
                    if p_class_val < 0.5:
                        continue
                    p_class = np.argmax(f_class[i][box_top_index[i][j]])
                    p_location = self.all_default_boxs[box_top_index[i][j]]
                    is_box_filter = False
                    for f_index in range(item_img_class) :
                        if self.jaccard(p_location,item_img_location[f_index]) > 0.3 and p_class == item_img_class[f_index] :
                            is_box_filter = True
                            break
                    if is_box_filter == False :
                        item_img_class.append(p_class)
                        item_img_class_val.append(p_class_val)
                        item_img_location.append(p_location)
                pred_class.append(item_img_class)
                pred_class_val.append(item_img_class_val)
                pred_location.append(item_img_location)
            return pred_class, pred_class_val, pred_location
            
    # Batch Normalization算法
    #批量归一标准化操作，预防梯度弥散、消失与爆炸
    def batch_normalization(self, input):
        bn_input_shape = input.get_shape()
        scale = tf.Variable(tf.ones([bn_input_shape[-1]]))
        beta = tf.Variable(tf.zeros([bn_input_shape[-1]]))
        pop_mean = tf.Variable(tf.zeros([bn_input_shape[-1]]), trainable=False)
        pop_var = tf.Variable(tf.ones([bn_input_shape[-1]]), trainable=False)
        if self.isTraining :
            batch_mean, batch_var = tf.nn.moments(input, list(range(len(bn_input_shape) - 1)))
            train_mean = tf.assign(pop_mean, pop_mean * self.conv_bn_decay + batch_mean * (1 - self.conv_bn_decay))
            train_var = tf.assign(pop_var, pop_var * self.conv_bn_decay + batch_var * (1 - self.conv_bn_decay))
            with tf.control_dependencies([train_mean, train_var]):
                return tf.nn.batch_normalization(input, batch_mean, batch_var, beta, scale, self.conv_bn_epsilon)
        else:
            return tf.nn.batch_normalization(input, pop_mean, pop_var, beta, scale, self.conv_bn_epsilon)
    
    # 初始化、整理训练数据
    def generate_all_default_boxs(self):
        # 全部按照比例计算并生成一张图像产生的每个default box的坐标以及长宽
        # 用于后续的jaccard匹配
        all_default_boxes = []
        for index, map_shape in zip(range(len(self.feature_maps_shape)), self.feature_maps_shape):
            width = map_shape[1]
            height = map_shape[2]
            scale = self.default_box_scale[index]
            ratios = self.box_aspect_ratio[index]
            for x in range(width):
                for y in range(height):
                    for i,ratio in zip(range(len(ratios)), ratios):
                        top_x = x / float(width)
                        top_y = y / float(height)
                        box_width = np.sqrt(scale * ratio)
                        box_height = np.sqrt(scale / ratio)
                        all_default_boxes.append([top_x, top_y, box_width, box_height])
        all_default_boxes = np.array(all_default_boxes)
        #检查数据是否正确
        all_default_boxes = self.check_numerics(all_default_boxes,'all_default_boxes') 
        return all_default_boxes

    # 整理生成groundtruth数据
    def generate_groundtruth_data(self, input_actual_data, f_class):
        # 生成空数组，用于保存groundtruth
        input_actual_data_len = len(input_actual_data)
        gt_class = np.zeros((input_actual_data_len, self.all_default_boxs_len)) 
        gt_positives = np.zeros((input_actual_data_len, self.all_default_boxs_len))
        gt_positives_weight = np.zeros((input_actual_data_len, self.all_default_boxs_len))
        gt_negatives = np.zeros((input_actual_data_len, self.all_default_boxs_len))
        # 初始化正例训练数据
        for img_index in range(input_actual_data_len):
            for pre_actual in input_actual_data[img_index]:
                gt_class_val = pre_actual[-1:][0]
                gt_box_val = pre_actual[:-1]
                for boxe_index in range(self.all_default_boxs_len):
                    jacc = self.jaccard(gt_box_val, self.all_default_boxs[boxe_index])
                    if jacc > self.jaccard_value or jacc == self.jaccard_value:
                        gt_class[img_index][boxe_index] = gt_class_val
                        gt_positives[img_index][boxe_index] = 1
                        gt_positives_weight[img_index][boxe_index] = (1 + jacc - self.jaccard_value)
                        gt_negatives[img_index][boxe_index] = 0
            # 正负例比值 1:2 
            gt_neg_end_count = int(np.sum(gt_positives[img_index]) * 2)
            if np.isnan(gt_neg_end_count) or gt_neg_end_count==0:
                gt_neg_end_count = 1
            if (gt_neg_end_count+np.sum(gt_positives[img_index])) > self.all_default_boxs_len :
                gt_neg_end_count = self.all_default_boxs_len - np.sum(gt_positives[img_index])
            # 随机选择负例
            gt_neg_index = np.random.randint(low=0, high=self.all_default_boxs_len, size=gt_neg_end_count)
            for r_index in gt_neg_index:
                if gt_positives[img_index][r_index]==0 and gt_negatives[img_index][r_index]==0: 
                    gt_class[img_index][r_index] = self.background_classes_val
                    gt_positives[img_index][r_index] = 0
                    gt_negatives[img_index][r_index] = 1
        #检查数据是否正确
        gt_class = self.check_numerics(gt_class,'gt_class')
        gt_positives = self.check_numerics(gt_positives,'gt_positives')
        gt_positives_weight = self.check_numerics(gt_positives_weight,'gt_positives_weight')
        gt_negatives = self.check_numerics(gt_negatives,'gt_negatives') 

        return gt_class, gt_positives, gt_positives_weight, gt_negatives

    # jaccard算法
    # 计算IOU，rect1、rect2格式为[min_x,min_y,width,height]           
    def jaccard(self, rect1, rect2):
        x_overlap = max(0, (min(rect1[0]+rect1[2], rect2[0]+rect2[2]) - max(rect1[0], rect2[0])))
        y_overlap = max(0, (min(rect1[1]+rect1[3], rect2[1]+rect2[3]) - max(rect1[1], rect2[1])))
        intersection = x_overlap * y_overlap
        area_box_a = rect1[2] * rect1[3]
        area_box_b = rect2[2] * rect2[3]
        union = area_box_a + area_box_b - intersection
        if intersection > 0 and union > 0 : 
            return intersection / union 
        else : 
            return 0

    # 检测数据是否正常
    def check_numerics(self, input_dataset, message):
        if str(input_dataset).find('Tensor') == 0 :
           input_dataset = tf.check_numerics(input_dataset, message)
        else :
            dataset = np.array(input_dataset)
            nan_count = np.count_nonzero(dataset != dataset) 
            inf_count = len(dataset[dataset == float("inf")])
            n_inf_count = len(dataset[dataset == float("-inf")])
            if nan_count>0 or inf_count>0 or n_inf_count>0:
                raise Exception('【'+ message +'】出现数据错误！【nan：'+str(nan_count)+'|inf：'+str(inf_count)+'|-inf：'+str(n_inf_count)+'】') 
        return  input_dataset
