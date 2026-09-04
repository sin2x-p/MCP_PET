import logging
import os
from typing import Optional

import httpx
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

mcp = FastMCP(name="biz-mcp-gateway", version="1.0.0")

# ============ API 配置（从环境变量读取） ============
API_BASE = "https://ai.inspirvision.cn/s"
TOKEN = os.environ.get("TOKEN", "")
TIMEOUT = 30


JSON_BODY_PATHS = {
    "/api/deletePetImageByImageId",
    "/api/petEvent",
    "/api/getPetArchivesList",
}


async def _post(path: str, data: dict, use_json: bool = False) -> dict:
    """统一的请求方法，处理鉴权、超时、错误"""
    if TOKEN:
        data["token"] = TOKEN
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            if use_json or path in JSON_BODY_PATHS:
                resp = await client.post(f"{API_BASE}{path}", json=data)
            else:
                resp = await client.post(f"{API_BASE}{path}", data=data)
            resp.raise_for_status()
            return resp.json()
    except httpx.TimeoutException:
        logger.error(f"请求超时: {path}")
        return {"error": "请求超时，请稍后重试"}
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP错误: {path} status={e.response.status_code}")
        return {"error": f"服务端返回错误: {e.response.status_code}"}
    except Exception as e:
        logger.exception(f"请求异常: {path}")
        return {"error": f"请求异常: {str(e)}"}


# ============ 医疗票据相关 ============

@mcp.tool()
async def invoice_check_all(
    invoice_code: str = "",
    invoice_number: str = "",
    check_code: str = "",
    pretax_amount: str = "",
    invoicing_date: str = "",
    payer: str = "",
    id_card_no: str = "",
    need_pdf: int = 1,
    img_base64: str = "",
) -> dict:
    """医疗电子发票查验（兼容版）。支持传图片或发票信息进行查验。

    Args:
        invoice_code: 发票代码
        invoice_number: 发票号码
        check_code: 校验码后6位
        pretax_amount: 发票金额
        invoicing_date: 开票日期，如 20240118
        payer: 交款人信息，一年以上票据必传
        id_card_no: 身份证后六位
        need_pdf: 是否需要明细（0不需要 1需要，默认1）
        img_base64: 图片base64编码(含data:image/png;base64,)，与发票信息二选一
    """
    return await _post("/api/ocr/invoiceCheckAll", {
        "invoiceCode": invoice_code,
        "invoiceNumber": invoice_number,
        "checkCode": check_code,
        "pretaxAmount": pretax_amount,
        "invoicingDate": invoicing_date,
        "payer": payer,
        "idCardNo": id_card_no,
        "needPdf": need_pdf,
        "imgBase64": img_base64,
    })


@mcp.tool()
async def qr_code_invoice_check(
    img_base64: str = "",
    id_card_no: str = "",
    invoicing_date: str = "",
    payer: str = "",
    need_pdf: int = 1,
) -> dict:
    """医疗票据查验（传图片识别发票信息后查验）

    Args:
        img_base64: 图片base64编码(含data:image/png;base64,)
        id_card_no: 身份证后六位，部分地区获取明细必填
        invoicing_date: 开票日期，如 20240118
        payer: 交款人信息，一年以上票据必传
        need_pdf: 是否需要明细（0不需要 1需要，默认1）
    """
    return await _post("/api/ocr/qrCodeInvoiceCheck", {
        "imgBase64": img_base64,
        "idCardNo": id_card_no,
        "invoicingDate": invoicing_date,
        "payer": payer,
        "needPdf": need_pdf,
    })


@mcp.tool()
async def invoice_check_match_all(
    img_base64: str = "",
    invoice_code: str = "",
    invoice_number: str = "",
    check_code: str = "",
    pretax_amount: str = "",
    invoicing_date: str = "",
    id_card_no: str = "",
    province: str = "",
    city: str = "",
) -> dict:
    """医疗电子发票查验-医保版

    Args:
        img_base64: 图片base64编码
        invoice_code: 发票代码
        invoice_number: 发票号码
        check_code: 校验码后6位
        pretax_amount: 发票金额
        invoicing_date: 开票日期
        id_card_no: 身份证后六位
        province: 省份，如 "江苏省"
        city: 城市，如 "南京市"
    """
    return await _post("/api/ocr/invoiceCheckMatchAll", {
        "imgBase64": img_base64,
        "invoiceCode": invoice_code,
        "invoiceNumber": invoice_number,
        "checkCode": check_code,
        "pretaxAmount": pretax_amount,
        "invoicingDate": invoicing_date,
        "idCardNo": id_card_no,
        "province": province,
        "city": city,
    })


@mcp.tool()
async def async_check_send(
    img_base64: str = "",
    invoice_code: str = "",
    invoice_number: str = "",
    check_code: str = "",
    pretax_amount: str = "",
    invoicing_date: str = "",
    payer: str = "",
    seller_number: int = 0,
    need_pdf: int = 1,
    id_card_no: str = "",
) -> dict:
    """异步医疗电子发票查验-提交任务

    Args:
        img_base64: 图片base64编码
        invoice_code: 发票代码
        invoice_number: 发票号码
        check_code: 校验码后6位
        pretax_amount: 发票金额
        invoicing_date: 开票日期
        payer: 交款人信息
        seller_number: 销售方识别号
        need_pdf: 是否需要明细
        id_card_no: 身份证后六位
    """
    return await _post("/api/ocr/sendAsyncCheckAll", {
        "imgBase64": img_base64,
        "invoiceCode": invoice_code,
        "invoiceNumber": invoice_number,
        "checkCode": check_code,
        "pretaxAmount": pretax_amount,
        "invoicingDate": invoicing_date,
        "payer": payer,
        "sellerNumber": seller_number,
        "needPdf": need_pdf,
        "idCardNo": id_card_no,
    })


@mcp.tool()
async def async_check_get(task_id: str) -> dict:
    """异步医疗电子发票查验-获取结果

    Args:
        task_id: 异步任务ID，由 async_check_send 返回
    """
    return await _post("/api/ocr/getAsyncCheckAll", {"taskId": task_id})


@mcp.tool()
async def financial_bill_check(
    invoice_code: str,
    invoice_number: str,
    pretax_amount: str,
    invoicing_date: str,
    check_code: str,
    payer: str = "",
    id_card_no: str = "",
    need_pdf: str = "1",
) -> dict:
    """医疗票据查验（必填发票信息）

    Args:
        invoice_code: 发票代码（必填）
        invoice_number: 发票号码（必填）
        pretax_amount: 发票金额（必填）
        invoicing_date: 开票日期（必填），如 20240118
        check_code: 校验码后6位（必填）
        payer: 交款人信息，一年以上票据必传
        id_card_no: 身份证后六位
        need_pdf: 是否需要明细（0不需要 1需要）
    """
    return await _post("/api/ocr/financialBillCheck", {
        "invoiceCode": invoice_code,
        "invoiceNumber": invoice_number,
        "pretaxAmount": pretax_amount,
        "invoicingDate": invoicing_date,
        "checkCode": check_code,
        "payer": payer,
        "idCardNo": id_card_no,
        "needPdf": need_pdf,
    })


# ============ 证件识别 ============

@mcp.tool()
async def identity_card(
    img_base64: str = "",
    crop_type: int = 0,
    detect_quality: int = 0,
    detect_risk: int = 0,
) -> dict:
    """身份证识别

    Args:
        img_base64: 图片base64编码(含data:image/png;base64,)
        crop_type: 0=实拍图 1=复印件
        detect_quality: 是否开启质量检测（0关闭 1开启）
        detect_risk: 是否开启风险检测（0关闭 1开启）
    """
    return await _post("/api/ocr/identityCard", {
        "imgBase64": img_base64,
        "cropType": crop_type,
        "detectQuality": detect_quality,
        "detectRisk": detect_risk,
    })


@mcp.tool()
async def bank_card(img_base64: str = "") -> dict:
    """银行卡识别

    Args:
        img_base64: 图片base64编码(含data:image/png;base64,)
    """
    return await _post("/api/ocr/bankCard", {"imgBase64": img_base64})


@mcp.tool()
async def business_license(img_base64: str = "") -> dict:
    """营业执照识别

    Args:
        img_base64: 图片base64编码(含data:image/png;base64,)
    """
    return await _post("/api/ocr/businessLicense", {"imgBase64": img_base64})


@mcp.tool()
async def passport(img_base64: str = "") -> dict:
    """护照识别（中国大陆地区）

    Args:
        img_base64: 图片base64编码(含data:image/png;base64,)
    """
    return await _post("/api/ocr/passport", {"imgBase64": img_base64})


@mcp.tool()
async def vehicle_license(img_base64: str = "", card_side: str = "FRONT") -> dict:
    """行驶证识别

    Args:
        img_base64: 图片base64编码
        card_side: FRONT=主页(默认) BACK=副页 ALL=主副页都识别
    """
    return await _post("/api/ocr/vehicleLicense", {
        "imgBase64": img_base64,
        "cardSide": card_side,
    })


@mcp.tool()
async def driving_license(img_base64: str = "", card_side: str = "FRONT") -> dict:
    """驾驶证识别

    Args:
        img_base64: 图片base64编码
        card_side: FRONT=主页(默认) BACK=副页
    """
    return await _post("/api/ocr/drivingLicense", {
        "imgBase64": img_base64,
        "cardSide": card_side,
    })


@mcp.tool()
async def account_book(img_base64: str = "", house_side: int = 0) -> dict:
    """户口本识别

    Args:
        img_base64: 图片base64编码
        house_side: 0=成员页(默认) 1=户主页
    """
    return await _post("/api/ocr/accountBook", {
        "imgBase64": img_base64,
        "houseSide": house_side,
    })


# ============ 医疗相关 ============

@mcp.tool()
async def medical_listing(
    img_base64: str = "",
    province: str = "",
    city: str = "",
    kd_use_flag: int = 0,
    medical_type: str = "",
) -> dict:
    """医疗费用清单识别

    Args:
        img_base64: 图片base64编码
        province: 省份名称
        city: 城市名称
        kd_use_flag: 是否知识库匹配（0否 1是）
        medical_type: 清单类型，不传自动识别
    """
    return await _post("/api/ocr/medicalListing", {
        "imgBase64": img_base64,
        "province": province,
        "city": city,
        "kdUseFlag": kd_use_flag,
        "medicalType": medical_type,
    })


@mcp.tool()
async def medical_invoice(
    img_base64: str = "",
    province: str = "",
    city: str = "",
    kd_use_flag: int = 0,
    medical_type: str = "",
) -> dict:
    """门诊住院发票识别

    Args:
        img_base64: 图片base64编码
        province: 省份名称
        city: 城市名称
        kd_use_flag: 是否知识库匹配（0否 1是）
        medical_type: 票据类型，不传自动识别
    """
    return await _post("/api/ocr/medical", {
        "imgBase64": img_base64,
        "province": province,
        "city": city,
        "kdUseFlag": kd_use_flag,
        "medicalType": medical_type,
    })


@mcp.tool()
async def discharge_abstract(img_base64: str = "", kd_use_flag: int = 0) -> dict:
    """病历单据识别

    Args:
        img_base64: 图片base64编码
        kd_use_flag: 是否知识库匹配（0否 1是）
    """
    return await _post("/api/ocr/dischargeAbstract", {
        "imgBase64": img_base64,
        "kdUseFlag": kd_use_flag,
    })


@mcp.tool()
async def inspection_report(img_base64: str = "", tct: str = "") -> dict:
    """化验单识别

    Args:
        img_base64: 图片base64编码
        tct: 是否TCT样式（1=TCT样式，默认0）
    """
    return await _post("/api/ocr/inspectionReport", {
        "imgBase64": img_base64,
        "TCT": tct,
    })


# ============ 通用能力 ============

@mcp.tool()
async def general_ocr(img_base64: str = "") -> dict:
    """通用文本识别

    Args:
        img_base64: 图片base64编码(含data:image/png;base64,)
    """
    return await _post("/api/ocr/general", {"imgBase64": img_base64})


@mcp.tool()
async def general_advanced_ocr(img_base64: str = "") -> dict:
    """通用文字识别高精版

    Args:
        img_base64: 图片base64编码(含data:image/png;base64,)
    """
    return await _post("/api/ocr/generalAdvanced", {"imgBase64": img_base64})


@mcp.tool()
async def text_check(img_base64: str = "", text_type: int = 0) -> dict:
    """文档清晰度检测

    Args:
        img_base64: 图片base64编码
        text_type: 检查类型（1=身份证图片检查，默认0）
    """
    return await _post("/api/ocr/textCheck", {
        "imgBase64": img_base64,
        "textType": text_type,
    })


@mcp.tool()
async def qr_code(img_base64: str = "") -> dict:
    """二维码识别

    Args:
        img_base64: 图片base64编码(含data:image/png;base64,)
    """
    return await _post("/api/ocr/qrCode", {"imgBase64": img_base64})


@mcp.tool()
async def seal_detect(img_base64: str = "") -> dict:
    """清单印章检测

    Args:
        img_base64: 图片base64编码
    """
    return await _post("/api/ocr/sealDetect", {"imgBase64": img_base64})


@mcp.tool()
async def pdf_to_image(
    img_base64: str = "",
    page_num: int = 1,
    convert_type: str = "fitz",
    dpi: int = 200,
) -> dict:
    """PDF/OFD转图片

    Args:
        img_base64: 文件base64编码
        page_num: 转换页数，0=全部，默认1
        convert_type: 转换方式 fitz/pdfbox/ofd
        dpi: 分辨率，默认200
    """
    return await _post("/api/ocr/pdfToImage", {
        "imgBase64": img_base64,
        "pageNum": page_num,
        "convertType": convert_type,
        "dpi": dpi,
    })


# ============ 保单相关 ============

@mcp.tool()
async def auto_insurance(img_base64: str = "", show_seal: str = "0") -> dict:
    """车险保单识别

    Args:
        img_base64: 图片base64编码
        show_seal: 是否印章检测（0不检测 默认 1检测）
    """
    return await _post("/api/ocr/policy/autoInsurance", {
        "imgBase64": img_base64,
        "showSeal": show_seal,
    })


@mcp.tool()
async def life_insurance(img_base64: str = "") -> dict:
    """寿险保单识别

    Args:
        img_base64: 图片base64编码
    """
    return await _post("/api/ocr/policy/lifeInsurance", {"imgBase64": img_base64})


# ============ 车辆相关 ============

@mcp.tool()
async def license_plate(img_base64: str = "") -> dict:
    """车牌识别

    Args:
        img_base64: 图片base64编码
    """
    return await _post("/api/ocr/licensePlate", {"imgBase64": img_base64})


@mcp.tool()
async def vehicle_vin(img_base64: str = "") -> dict:
    """车辆VIN码识别

    Args:
        img_base64: 图片base64编码
    """
    return await _post("/api/ocr/vin", {"imgBase64": img_base64})


@mcp.tool()
async def vin_parsing(vin: str) -> dict:
    """车辆VIN码解析

    Args:
        vin: 车辆VIN码/车架号
    """
    return await _post("/api/ocr/vinParsing", {"vin": vin})


@mcp.tool()
async def vehicle_registration(img_base64: str = "") -> dict:
    """机动车登记证书识别

    Args:
        img_base64: 图片base64编码
    """
    return await _post("/api/ocr/vehicleRegistration", {"imgBase64": img_base64})


# ============ 知识库 ============

@mcp.tool()
async def get_knowledge(
    query_name: str,
    db_type: int = 0,
    accurate: int = 1,
    province: str = "",
    city: str = "",
    top: int = 5,
) -> dict:
    """医疗知识库查询

    Args:
        query_name: 查询名称（必填）
        db_type: 查询类目（1=药品 2=耗材 3=医疗服务 4=医疗机构 5=手术 6=疾病），0=全部
        accurate: 是否精准查询（0否 1是）
        province: 省份，不传全国
        city: 城市，不传全国
        top: 返回条数 1-100，默认5
    """
    return await _post("/api/ocr/getKnowledge", {
        "queryName": query_name,
        "dbType": db_type,
        "accurate": accurate,
        "province": province,
        "city": city,
        "top": top,
    })


# ============ 宠物相关 ============

@mcp.tool()
async def pet_type(
    img_base64: str = "",
    image_url: str = "",
    pet_type: int = 0,
    top_k: int = 3,
) -> dict:
    """宠物品种识别（识别猫/狗品种）

    Args:
        img_base64: 图片base64编码
        image_url: 图片URL地址
        pet_type: 宠物类别：0为狗 1为猫
        top_k: 返回前K个品种，默认3，最大10
    """
    return await _post("/api/petType", {
        "imageBase64": img_base64,
        "imageUrl": image_url,
        "petType": pet_type,
        "topK": top_k,
    })


@mcp.tool()
async def pet_act(
    img_base64: str = "",
    image_url: str = "",
    recognition_types: int = 0,
) -> dict:
    """宠物行为识别

    Args:
        img_base64: 图片base64编码(不能带data:image/png;base64头)
        image_url: 图片URL地址
        recognition_types: 识别类型，可多传，0=全部识别，默认0
    """
    return await _post("/api/things/petAct", {
        "imageBase64": img_base64,
        "imageUrl": image_url,
        "recognitionTypes": recognition_types,
    })


@mcp.tool()
async def create_pet_archives(
    img_base64: str = "",
    image_url: str = "",
    pet_id: str = "",
    mode: int = 0,
    group_id: str = "",
    recog_type: int = 0,
    compare_level: int = 2,
    mark: str = "",
    nickname: str = "",
    gender: int = 0,
    date_of_birth: str = "",
    birth_control_status: int = 0,
    is_verification: int = 1,
) -> dict:
    """宠物鼻纹+脸创建档案

    Args:
        img_base64: 图片base64编码
        image_url: 图片URL地址
        pet_id: 宠物档案ID，新建时不传；已有档案追加图片时传入
        mode: 拍摄模式，0 横屏(默认) 1 夜间
        group_id: 组ID，最长64字符，为空系统自动分配
        recog_type: 识别种类：0鼻纹(默认) 1脸部
        compare_level: 比对精细度 1(非常精细) 2(比较精细 默认) 3(比较宽松) 4(非常宽松)
        mark: 备注信息，最多265字符
        nickname: 宠物昵称，最多32字符
        gender: 性别 0为公 1为母
        date_of_birth: 出生日期，yyyy-MM-dd格式
        birth_control_status: 绝育状态 0为未 1为已
        is_verification: 是否开启唯一性校验 0不校验 1校验(默认)
    """
    return await _post("/api/createPetArchives", {
        "imageBase64": img_base64,
        "imageUrl": image_url,
        "petId": pet_id,
        "mode": mode,
        "groupId": group_id,
        "recogType": recog_type,
        "compareLevel": compare_level,
        "mark": mark,
        "nickname": nickname,
        "gender": gender,
        "dateOfBirth": date_of_birth,
        "birthControlStatus": birth_control_status,
        "isVerification": is_verification,
    })


@mcp.tool()
async def create_pet_archives_from_dog_face(
    img_base64: str = "",
    image_url: str = "",
    pet_id: str = "",
    mode: int = 0,
    group_id: str = "",
    mark: str = "",
    nickname: str = "",
    gender: int = 0,
    date_of_birth: str = "",
    birth_control_status: int = 0,
    is_verification: int = 1,
) -> dict:
    """狗脸创建宠物档案

    Args:
        img_base64: 图片base64编码
        image_url: 图片URL地址
        pet_id: 宠物档案ID
        mode: 拍摄模式，0 横屏(默认) 1 夜间
        group_id: 组ID，为空系统自动分配
        mark: 备注信息
        nickname: 宠物昵称
        gender: 性别 0为公 1为母
        date_of_birth: 出生日期，yyyy-MM-dd
        birth_control_status: 绝育状态 0未 1已
        is_verification: 唯一性校验 0不校验 1校验(默认)
    """
    return await _post("/api/createPetArchivesFromDogFace", {
        "imageBase64": img_base64,
        "imageUrl": image_url,
        "petId": pet_id,
        "mode": mode,
        "groupId": group_id,
        "mark": mark,
        "nickname": nickname,
        "gender": gender,
        "dateOfBirth": date_of_birth,
        "birthControlStatus": birth_control_status,
        "isVerification": is_verification,
    })


@mcp.tool()
async def create_pet_archives_from_cat_face(
    img_base64: str = "",
    image_url: str = "",
    pet_id: str = "",
    mode: int = 0,
    group_id: str = "",
    mark: str = "",
    nickname: str = "",
    gender: int = 0,
    date_of_birth: str = "",
    birth_control_status: int = 0,
    is_verification: int = 1,
) -> dict:
    """猫脸创建宠物档案

    Args:
        img_base64: 图片base64编码
        image_url: 图片URL地址
        pet_id: 宠物档案ID，新建时不传；已有档案追加图片时传入
        mode: 拍摄模式，0 横屏(默认) 1 夜间
        group_id: 组ID，为空系统自动分配
        mark: 备注信息
        nickname: 宠物昵称
        gender: 性别 0为公 1为母
        date_of_birth: 出生日期，yyyy-MM-dd
        birth_control_status: 绝育状态 0未 1已
        is_verification: 唯一性校验 0不校验 1校验(默认)
    """
    return await _post("/api/createPetArchivesFromCatFace", {
        "imageBase64": img_base64,
        "imageUrl": image_url,
        "petId": pet_id,
        "mode": mode,
        "groupId": group_id,
        "mark": mark,
        "nickname": nickname,
        "gender": gender,
        "dateOfBirth": date_of_birth,
        "birthControlStatus": birth_control_status,
        "isVerification": is_verification,
    })


@mcp.tool()
async def upload_pet_image(
    img_base64: str = "",
    image_url: str = "",
    group_id: str = "",
) -> dict:
    """上传图片获取路径

    Args:
        img_base64: 图片base64编码
        image_url: 图片URL地址
        group_id: 组ID，为空系统自动分配
    """
    return await _post("/api/uploadPetImage", {
        "imageBase64": img_base64,
        "imageUrl": image_url,
        "groupId": group_id,
    })


@mcp.tool()
async def upload_pet_image_find_pet_id(
    img_base64: str = "",
    image_url: str = "",
    group_id: str = "",
    pet_type: int = 0,
    recog_type: int = 0,
    top_k: int = 1,
) -> dict:
    """1:N 搜索匹配（上传图片在库中搜索最相似的宠物）

    Args:
        img_base64: 图片base64编码
        image_url: 图片URL地址
        group_id: 组ID，为空查全部，固定值all查全部
        pet_type: 宠物类别：0为狗 1为猫（必填）
        recog_type: 识别种类：0为鼻纹 1为脸部（必填）
        top_k: 最大返回结果数，默认1
    """
    return await _post("/api/uploadPetImageFindPeytId", {
        "imageBase64": img_base64,
        "imageUrl": image_url,
        "groupId": group_id,
        "petType": pet_type,
        "recogType": recog_type,
        "topK": top_k,
    })


@mcp.tool()
async def check_pet_image_and_pet_id(
    img_base64: str = "",
    image_url: str = "",
    group_id: str = "",
    pet_id: str = "",
    pet_type: str = "0",
    recog_type: str = "0",
) -> dict:
    """1:1 身份验证（验证图片是否为指定宠物）

    Args:
        img_base64: 图片base64编码
        image_url: 图片URL地址
        group_id: 组ID，为空系统自动分配
        pet_id: 宠物档案ID（必填）
        pet_type: 宠物类别：0为狗 1为猫
        recog_type: 识别种类：0为鼻纹 1为脸部
    """
    return await _post("/api/checkPetImageAndPeytId", {
        "imageBase64": img_base64,
        "imageUrl": image_url,
        "groupId": group_id,
        "petId": pet_id,
        "petType": pet_type,
        "recogType": recog_type,
    })


@mcp.tool()
async def delete_pet_image(
    pet_id: str,
    img_index: str,
    group_id: str,
    mode: str = "0",
) -> dict:
    """删除宠物档案图片

    Args:
        pet_id: 宠物档案ID（必填）
        img_index: 图片编号，传-1删除整个petId（必填）
        group_id: 组ID（必填）
        mode: 拍摄模式 0 横屏(默认) 1 夜间
    """
    return await _post("/api/deletePetImageByImageId", {
        "petId": pet_id,
        "imgIndex": img_index,
        "groupId": group_id,
        "mode": mode,
    })


@mcp.tool()
async def pet_event(
    pet_id: str,
    event_type: str,
    pet_type: int = 0,
    group_id: str = "",
    mode: str = "0",
) -> dict:
    """宠物事件（确认或回滚档案创建）

    Args:
        pet_id: 宠物档案ID（必填）
        event_type: 事件类型，rollback 或 commit（必填）
        pet_type: 宠物类型：0为狗 1为猫
        group_id: 组ID，为空系统自动分配
        mode: 拍摄模式 0 横屏(默认) 1 夜间
    """
    return await _post("/api/petEvent", {
        "petId": pet_id,
        "eventType": event_type,
        "petType": pet_type,
        "groupId": group_id,
        "mode": mode,
    })


@mcp.tool()
async def get_pet_archives_list(
    group_id: str = "",
    pet_id: str = "",
    pet_type: int = 0,
    page_num: int = 1,
    page_size: int = 10,
) -> dict:
    """档案列表筛选

    Args:
        group_id: 组ID，为空查当前用户，fixed值all查全部
        pet_id: 宠物档案ID
        pet_type: 宠物类别，0狗 1猫
        page_num: 页码，默认第一页
        page_size: 每页数量，默认10，最大100
    """
    return await _post("/api/getPetArchivesList", {
        "groupId": group_id,
        "petId": pet_id,
        "petType": pet_type,
        "pageNum": page_num,
        "pageSize": page_size,
    })


@mcp.tool()
async def cat_checking(
    img_base64: str = "",
    image_url: str = "",
    texture_type: str = "",
) -> dict:
    """猫关键点检测

    Args:
        img_base64: 图片base64编码(含data:image/png;base64,)
        image_url: 图片URL地址
        texture_type: 贴图样式，支持：sunglasses_1, sunglasses_3, weep1, weep2, weep3
    """
    return await _post("/api/catChecking", {
        "imgBase64": img_base64,
        "imgUrl": image_url,
        "textureType": texture_type,
    })


@mcp.tool()
async def dog_checking(
    img_base64: str = "",
    image_url: str = "",
    texture_type: str = "",
) -> dict:
    """狗关键点检测

    Args:
        img_base64: 图片base64编码(含data:image/png;base64,)
        image_url: 图片URL地址
        texture_type: 贴图样式，支持：sunglasses_1, sunglasses_3, weep1, weep2, weep3
    """
    return await _post("/api/dogChecking", {
        "imgBase64": img_base64,
        "imgUrl": image_url,
        "textureType": texture_type,
    })


@mcp.tool()
async def pet_detect(
    img_base64: str = "",
    image_url: str = "",
) -> dict:
    """猫狗全身关键点识别

    Args:
        img_base64: 图片base64编码(不能带data:image/png;base64头)
        image_url: 图片URL地址
    """
    return await _post("/api/petDetect", {
        "imageBase64": img_base64,
        "imageUrl": image_url,
    })


@mcp.tool()
async def pet_detect_furbo(
    img_base64: str = "",
    image_url: str = "",
) -> dict:
    """猫狗脸部关键点识别

    Args:
        img_base64: 图片base64编码(不能带data:image/png;base64头)
        image_url: 图片URL地址
    """
    return await _post("/api/petDetectFurbo", {
        "imageBase64": img_base64,
        "imageUrl": image_url,
    })


@mcp.tool()
async def cat_limb_checking(
    img_base64: str = "",
    image_url: str = "",
) -> dict:
    """猫四肢关键点检测

    Args:
        img_base64: 图片base64编码(含data:image/png;base64,)
        image_url: 图片URL地址
    """
    return await _post("/api/catLimbChecking", {
        "imgBase64": img_base64,
        "imgUrl": image_url,
    })


@mcp.tool()
async def dog_limb_checking(
    img_base64: str = "",
    image_url: str = "",
) -> dict:
    """狗四肢关键点检测

    Args:
        img_base64: 图片base64编码(含data:image/png;base64,)
        image_url: 图片URL地址
    """
    return await _post("/api/dogLimbChecking", {
        "imgBase64": img_base64,
        "imgUrl": image_url,
    })


@mcp.tool()
async def pet_leash_video_detect(video_base64: str) -> dict:
    """牵引绳检测（视频）

    Args:
        video_base64: 视频base64编码，大小不超过50M（必填）
    """
    return await _post("/api/petLeashVideoDetect", {"file": video_base64})


def main():
    """MCP 服务入口，支持 stdio 和 http 两种模式"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "http":
        # http 模式：本地部署或自有服务器
        logger.info("Starting biz-mcp-gateway (http mode) ...")
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=8000,
            path="/mcp",
        )
    else:
        # stdio 模式：魔搭等云平台托管
        logger.info("Starting biz-mcp-gateway (stdio mode) ...")
        mcp.run()


if __name__ == "__main__":
    main()
