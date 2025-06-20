from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot.keyboards import hr_main_kb, vacancy_inline_kb
from services import CompanyService, VacancyService

router = Router(name="company_admin")


# создание компании


class CreateCompany(StatesGroup):
    waiting_for_title = State()


@router.message(Command("newcompany"))
@router.message(F.text == "🏢 Создать компанию")
async def start_create_company(m: Message, state: FSMContext) -> None:
    await m.answer("Введите название компании:")
    await state.set_state(CreateCompany.waiting_for_title)


@router.message(CreateCompany.waiting_for_title)
async def save_company_title(m: Message, state: FSMContext) -> None:
    title = m.text.strip()
    await CompanyService.create_company(owner_id=m.from_user.id, title=title)

    await m.answer(
        "Компания создана ✅",
        reply_markup=await hr_main_kb(m.from_user.id),
    )
    await state.clear()


# создание вакансии


class CreateVacancy(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()


@router.message(F.text == "➕ Создать вакансию")
async def start_create_vacancy(m: Message, state: FSMContext) -> None:
    companies = await CompanyService.companies_for_user(m.from_user.id)
    if not companies:
        await m.answer(
            "У вас пока нет компаний.\n"
            "Сначала создайте её командой /newcompany или кнопкой «🏢 Создать компанию».",
        )
        return

    await m.answer("Введите название вакансии:")
    await state.set_state(CreateVacancy.waiting_for_title)


@router.message(CreateVacancy.waiting_for_title)
async def receive_vacancy_title(m: Message, state: FSMContext) -> None:
    await state.update_data(title=m.text.strip())
    await m.answer("Введите описание вакансии (или «-», чтобы оставить пустым):")
    await state.set_state(CreateVacancy.waiting_for_description)


@router.message(CreateVacancy.waiting_for_description)
async def receive_vacancy_description(m: Message, state: FSMContext) -> None:
    data = await state.get_data()
    title = data["title"]
    description = "" if m.text.strip() == "-" else m.text.strip()

    companies = await CompanyService.companies_for_user(m.from_user.id)
    if not companies:
        await m.answer("Похоже, у вас уже нет компаний — сначала создайте компанию.")
        await state.clear()
        return

    await VacancyService.create(
        company_id=companies[0].id,
        title=title,
        description=description,
    )

    await m.answer(
        "Вакансия создана ✅",
        reply_markup=await hr_main_kb(m.from_user.id),
    )
    await state.clear()


# редактирование вакансии


class EditVacancy(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()


@router.message(F.text == "✏️ Редактировать вакансии")
async def start_edit_vacancy(m: Message, state: FSMContext) -> None:
    companies = await CompanyService.companies_for_user(m.from_user.id)
    if not companies or not any(c.vacancies for c in companies):
        await m.answer("У вас пока нет вакансий для редактирования.")
        return

    await m.answer(
        "Выберите вакансию для редактирования:",
        reply_markup=await vacancy_inline_kb(owner_id=m.from_user.id, mode="edit"),
    )


# выбор вакансии
@router.callback_query(F.data.startswith("edit_"))
async def choose_vacancy(cb: CallbackQuery) -> None:
    vac_id = int(cb.data.split("_", 1)[1])
    vac = await VacancyService.by_id(vac_id)

    if not vac or vac.company.owner_id != cb.from_user.id:
        await cb.answer("Недоступно", show_alert=True)
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Изменить название", callback_data=f"rename_{vac_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📝 Изменить описание", callback_data=f"desc_{vac_id}"
                )
            ],
        ]
    )
    await cb.message.answer("Что хотите изменить?", reply_markup=kb)
    await cb.answer()


# переименование
@router.callback_query(F.data.startswith("rename_"))
async def ask_new_title(cb: CallbackQuery, state: FSMContext) -> None:
    vac_id = int(cb.data.split("_", 1)[1])
    await state.update_data(vacancy_id=vac_id)
    await state.set_state(EditVacancy.waiting_for_title)
    await cb.message.answer("Введите новое название вакансии:")
    await cb.answer()


@router.message(EditVacancy.waiting_for_title)
async def save_new_title(m: Message, state: FSMContext) -> None:
    vac_id = (await state.get_data())["vacancy_id"]
    await VacancyService.update_title(vacancy_id=vac_id, title=m.text)
    await m.answer(
        "Название обновлено ✅",
        reply_markup=await hr_main_kb(m.from_user.id),
    )
    await state.clear()


# изменение описания
@router.callback_query(F.data.startswith("desc_"))
async def ask_new_description(cb: CallbackQuery, state: FSMContext) -> None:
    vac_id = int(cb.data.split("_", 1)[1])
    await state.update_data(vacancy_id=vac_id)
    await state.set_state(EditVacancy.waiting_for_description)
    await cb.message.answer(
        "Введите новое описание вакансии (или «-», чтобы оставить пустым):"
    )
    await cb.answer()


@router.message(EditVacancy.waiting_for_description)
async def save_new_description(m: Message, state: FSMContext) -> None:
    vac_id = (await state.get_data())["vacancy_id"]
    description = "" if m.text.strip() == "-" else m.text.strip()
    await VacancyService.update_description(vacancy_id=vac_id, description=description)
    await m.answer(
        "Описание обновлено ✅",
        reply_markup=await hr_main_kb(m.from_user.id),
    )
    await state.clear()
