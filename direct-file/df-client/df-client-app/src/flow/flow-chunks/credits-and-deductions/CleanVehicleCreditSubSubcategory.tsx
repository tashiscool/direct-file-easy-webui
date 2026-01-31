/* eslint-disable max-len */
import { Gate, Screen, SubSubcategory, Assertion } from '../../flowDeclarations.js';
import {
  Boolean,
  ContextHeading,
  DFModal,
  Dollar,
  Heading,
  InfoDisplay,
  LimitingString,
  SaveAndOrContinueButton,
  IconDisplay,
  DFAlert,
  Enum,
} from '../../ContentDeclarations.js';

/**
 * Clean Vehicle Credit SubSubcategory
 * Handles Form 8936 clean vehicle credits (new and used EVs)
 */
export const CleanVehicleCreditSubSubcategory = (
  <SubSubcategory route='clean-vehicle' headingLevel='h2' borderStyle='heavy'>
    <Gate condition='/flowTrue'>
      <Screen route='clean-vehicle-intro'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/credits-and-deductions/credits/clean-vehicle' />
        <Heading i18nKey='/heading/credits-and-deductions/credits/clean-vehicle/intro' />
        <InfoDisplay i18nKey='/info/credits-and-deductions/credits/clean-vehicle/description' />
        <DFModal i18nKey='/info/credits-and-deductions/credits/clean-vehicle/eligibility' />
        <Boolean path='/purchasedCleanVehicle' />
        <SaveAndOrContinueButton />
      </Screen>
      <Gate condition='/purchasedCleanVehicle'>
        <Screen route='clean-vehicle-type'>
          <ContextHeading displayOnlyOn='edit' i18nKey='/heading/credits-and-deductions/credits/clean-vehicle' />
          <Heading i18nKey='/heading/credits-and-deductions/credits/clean-vehicle/type' />
          <InfoDisplay i18nKey='/info/credits-and-deductions/credits/clean-vehicle/new-vs-used' />
          <Enum path='/cleanVehicleType' />
          <SaveAndOrContinueButton />
        </Screen>
        <Screen route='clean-vehicle-vin'>
          <ContextHeading displayOnlyOn='edit' i18nKey='/heading/credits-and-deductions/credits/clean-vehicle' />
          <Heading i18nKey='/heading/credits-and-deductions/credits/clean-vehicle/vin' />
          <InfoDisplay i18nKey='/info/credits-and-deductions/credits/clean-vehicle/vin-info' />
          <LimitingString path='/cleanVehicleVIN' />
          <SaveAndOrContinueButton />
        </Screen>
        <Screen route='clean-vehicle-purchase-price'>
          <ContextHeading displayOnlyOn='edit' i18nKey='/heading/credits-and-deductions/credits/clean-vehicle' />
          <Heading i18nKey='/heading/credits-and-deductions/credits/clean-vehicle/price' />
          <DFModal i18nKey='/info/credits-and-deductions/credits/clean-vehicle/price-limits' />
          <Dollar path='/cleanVehiclePurchasePrice' />
          <SaveAndOrContinueButton />
        </Screen>
        <Assertion
          type='success'
          i18nKey='dataviews./flow/credits-and-deductions/credits.assertions.cleanVehicleQualified'
          condition='/cleanVehicleCreditQualified'
        />
        <Screen route='clean-vehicle-qualified' condition='/cleanVehicleCreditQualified'>
          <ContextHeading displayOnlyOn='edit' i18nKey='/heading/credits-and-deductions/credits/clean-vehicle' />
          <Heading i18nKey='/heading/credits-and-deductions/credits/clean-vehicle/qualified' />
          <InfoDisplay i18nKey='/info/credits-and-deductions/credits/clean-vehicle/credit-amount' />
          <DFAlert
            i18nKey='/info/credits-and-deductions/credits/clean-vehicle/credit-info'
            headingLevel='h3'
            type='success'
          />
          <SaveAndOrContinueButton />
        </Screen>
      </Gate>
    </Gate>
  </SubSubcategory>
);
