'use strict'
/**
 * This file is a trimmed down version of the fitCreator.ts, which can be found at {@link https://github.com/JaapvanEkris/openrowingmonitor|OpenRowingMonitor}
 *
 * @file This module generates the fit-file content for a recorded rowing session: it contains
 * the session and the strokes (records) as defined by the Garmin fit and rowing data standard specifications.
 * It assumes that something persistsed every stroke, split, and interval, and this module reads a
 * session back and encodes it in the fit format. sessionToFit(sessionId) is the entry point.
 *
 * This uses 'Smart Recording' per stroke as that makes sure that per-stroke data can also be extracted from the file (like work per stroke)
 * The RowingDtata standard calls this 'Stroke-Boundary Recording', which is assumed to be managed by the recorder.
 * @see {@link https://developer.garmin.com/fit/file-types/activity/|the fields and their meaning}.
 * @see {@link https://github.com/markw65/fit-file-writer/blob/main/src/fit-tables.ts|for a list of all available fields and their types}.
 * @see {@link https://developer.garmin.com/fit/cookbook/encoding-activity-files/|the description of the filestructure and how timestamps}
 * @see {@link https://forums.garmin.com/developer/fit-sdk/b/news-announcements/posts/important-fit-activity-file-message-change|description of the timestamps for summary messages}
 * @see {@link https://developer.garmin.com/fit/cookbook/durations/|how the different times are defined}
 * @see {@link https://github.com/MoveLab-Studio/rowing-data-standard/blob/main/spec/FIT_STANDARD.md|the harmonised rowing data FIT specifications for definitions and interpretations}
 * We use 'summary last message sequencing' as the stream makes most sense that way
 * As general timestamp we use the session end time, as that is semantically more sound than Garmin's approach of the session start time
 *
 * BE AWARE: general rowing and Garmin FIT terminology conflict:
 * - a fit-file 'split' is written from a rowing interval, and
 * - a fit-file 'lap' from a rowing split.
 */
import log from 'loglevel'
import { FitWriter, fit_messages } from '@markw65/fit-file-writer'
import { createDatabase } from './utils/store.ts'
import type { Session, Interval, Split, Stroke } from './utils/store.ts'

/** Everything of a session the fit encoding consumes, as read from the store. */
interface WorkoutData {
  session: Session
  intervals: Interval[]
  splits: Split[]
  strokes: Stroke[]
}

/** A developer field value as the FitWriter takes it. */
interface DeveloperFieldValue {
  developer_data_index: number
  field_num: number
  value: number | number[]
}

/**
 * @description Reads the session from the database and returns its fit-file
 * content, or undefined when the session is unknown or has no usable data.
 * Opens (and closes) its own store connection.
 */
export async function sessionToFit (sessionId: number, dbPath?: string): Promise<DataView | undefined> {
  const store = createDatabase(dbPath)
  try {
    const session = store.getSession(sessionId)
    if (session === undefined) {
      log.error(`fitRecorder: unknown session ${sessionId}`)
      return undefined
    }
    if (session.complete === null || !((session.complete ?? 0) > 0)) {
      log.debug(`fitRecorder: session ${sessionId} is not marked complete (yet), is the session still active?`)
      return undefined
    }
    if (session.endTime === null || !((session.totalMovingTime ?? 0) > 0) || !((session.totalLinearDistance ?? 0) > 0)) {
      log.debug(`fitRecorder: session ${sessionId} has no usable data for a fit-file`)
      return undefined
    }
    const workout: WorkoutData = {
      session,
      intervals: store.getIntervals(sessionId),
      splits: store.getSplits(sessionId),
      strokes: store.getStrokesWithBoundaries(sessionId)
    }
    return await workoutToFit(workout)
  } finally {
    store.close()
  }
}

/**
 * @description This function generates the entire fit-file from the session's
 * database rows. We use 'summary last message sequencing' as the stream makes
 * most sense that way.
 */
export async function workoutToFit (workout: WorkoutData): Promise<DataView | undefined> {
  const { session, splits } = workout
  const fitWriter = new FitWriter()
  // The number of points of the force curve, which is also the size of the HandleForceCurve array (the FIT limit is 127 points)
  const maxForceCurvePointCount = Math.min(session.maxForceCurveLength ?? 0, 127)

  // The file header
  fitWriter.writeMessage(
    'file_id',
    {
      time_created: fitWriter.time(new Date(session.endTime as number)),
      type: 'activity',
      manufacturer: 'development',
      product: 0,
      number: 0
    },
    null,
    true
  )

  fitWriter.writeMessage(
    'file_creator',
    {
      software_version: 1
    },
    null,
    true
  )

  /**
   * Register the developer data source and developer fields
   * @see {@link https://github.com/MoveLab-Studio/rowing-data-standard/blob/main/spec/FIT_STANDARD.md|the harmonised rowing data FIT specifications for definitions and more information}
   */
  fitWriter.writeMessage(
    'developer_data_id',
    {
      application_id: '89e86158-6d47-5c98-9d46-7d29437f27b9'
        .replace(/-/g, '')
        .match(/../g)
        .map((s) => parseInt(s, 16)),
      developer_data_index: 0,
      // The protocol version of the rowing data standard, not the software version
      application_version: 1
    },
    null,
    true
  )

  // Registering each developer field individually
  fitWriter.writeMessage(
    'field_description',
    {
      developer_data_index: 0,
      field_definition_number: 0,
      fit_base_type_id: 'uint16',
      field_name: 'DriveLength',
      scale: 1,
      units: 'mm'
    },
    null,
    true
  )

  fitWriter.writeMessage(
    'field_description',
    {
      developer_data_index: 0,
      field_definition_number: 1,
      fit_base_type_id: 'uint16',
      field_name: 'StrokeDriveTime',
      scale: 1,
      units: 'ms'
    },
    null,
    true
  )

  fitWriter.writeMessage(
    'field_description',
    {
      developer_data_index: 0,
      field_definition_number: 2,
      fit_base_type_id: 'uint16',
      field_name: 'DragFactor',
      scale: 1,
    },
    null,
    true
  )

  fitWriter.writeMessage(
    'field_description',
    {
      developer_data_index: 0,
      field_definition_number: 3,
      fit_base_type_id: 'uint16',
      field_name: 'StrokeRecoveryTime',
      scale: 1,
      units: 'ms'
    },
    null,
    true
  )

  // Write the Force curve dependent values only when there is a force curve to report
  if (maxForceCurvePointCount > 0) {
    fitWriter.writeMessage(
      'field_description',
      {
        developer_data_index: 0,
        field_definition_number: 6,
        fit_base_type_id: 'uint16',
        field_name: 'AverageDriveForce',
        scale: 10,
        units: 'N'
      },
      null,
      true
    )

    fitWriter.writeMessage(
      'field_description',
      {
        developer_data_index: 0,
        field_definition_number: 7,
        fit_base_type_id: 'uint16',
        field_name: 'PeakDriveForce',
        scale: 10,
        units: 'N'
      },
      null,
      true
    )
  }

  fitWriter.writeMessage(
    'field_description',
    {
      developer_data_index: 0,
      field_definition_number: 8,
      fit_base_type_id: 'uint16',
      field_name: 'AverageBoatSpeed',
      scale: 100,
      units: 'm/s'
    },
    null,
    true
  )

  fitWriter.writeMessage(
    'field_description',
    {
      developer_data_index: 0,
      field_definition_number: 9,
      fit_base_type_id: 'uint8',
      field_name: 'WorkoutState',
      scale: 1
    },
    null,
    true
  )

  fitWriter.writeMessage(
    'field_description',
    {
      developer_data_index: 0,
      field_definition_number: 10,
      fit_base_type_id: 'uint8',
      field_name: 'RecordingStrategy',
      scale: 1
    },
    null,
    true
  )

  // Write the Force curve dependent values only when there is a force curve to report
  if (maxForceCurvePointCount > 0) {
    fitWriter.writeMessage(
      'field_description',
      {
        developer_data_index: 0,
        field_definition_number: 17,
        fit_base_type_id: 'uint16',
        field_name: 'PeakForcePositionNorm',
        scale: 100,
        units: '%'
      },
      null,
      true
    )

    fitWriter.writeMessage(
      'field_description',
      {
        developer_data_index: 0,
        field_definition_number: 18,
        fit_base_type_id: 'uint16',
        field_name: 'PeakForcePositionAbs',
        scale: 1,
        units: 'mm'
      },
      null,
      true
    )
  }

  fitWriter.writeMessage(
    'field_description',
    {
      developer_data_index: 0,
      field_definition_number: 19,
      fit_base_type_id: 'uint16',
      field_name: 'StrokeWork',
      scale: 1,
      units: 'J'
    },
    null,
    true
  )

  // Write the Force curve dependent values only when there is a force curve to report
  if (maxForceCurvePointCount > 0) {
    fitWriter.writeMessage(
      'field_description',
      {
        developer_data_index: 0,
        field_definition_number: 60,
        fit_base_type_id: 'uint16',
        array: maxForceCurvePointCount,
        scale: 10,
        field_name: 'HandleForceCurve',
        units: 'N'
      },
      null,
      true
    )

    fitWriter.writeMessage(
      'field_description',
      {
        developer_data_index: 0,
        field_definition_number: 90,
        fit_base_type_id: 'uint8',
        field_name: 'InstrokeAbscissaType',
        scale: 1
      },
      null,
      true
    )

    fitWriter.writeMessage(
      'field_description',
      {
        developer_data_index: 0,
        field_definition_number: 91,
        fit_base_type_id: 'uint16',
        field_name: 'InstrokeSampleInterval',
        scale: 1,
        units: 'mm'
      },
      null,
      true
    )

    fitWriter.writeMessage(
      'field_description',
      {
        developer_data_index: 0,
        field_definition_number: 92,
        fit_base_type_id: 'uint8',
        field_name: 'InstrokePointCount',
        scale: 1
      },
      null,
      true
    )
  }

  // Activity summary
  fitWriter.writeMessage(
    'activity',
    {
      timestamp: fitWriter.time(new Date(session.endTime as number)),
      local_timestamp: fitWriter.time(new Date(session.startTime)) - new Date(session.startTime).getTimezoneOffset() * 60,
      ...(session.totalTime != undefined && session.totalTime >= 0 && session.totalTime < 4294967295 ? { total_timer_time: session.totalTime / 1000 } : {}),
      num_sessions: 1,
      event: 'activity',
      event_type: 'stop',
      type: 'manual'
    },
    null,
    true
  )

  // BE AWARE: the manufacturer name currently prevents issues with certain consumers, as these tend to relax parsing requirements!
  fitWriter.writeMessage(
    'device_info',
    {
      timestamp: fitWriter.time(new Date(session.endTime as number)),
      device_index: 0,
      device_type: 0,
      manufacturer: 'development',
      product_name: 'OpenRowingMonitor'
    },
    null,
    true
  )

  fitWriter.writeMessage(
    'sport',
    {
      sport: 'rowing',
      sub_sport: 'indoorRowing',
      name: 'Indoor rowing'
    },
    null,
    true
  )

  /*
   * The session summary
   * Several parameters are calculated at the closure of the session, or after it by a postprocessing run. These should be called with caution																																		  
   */
  const developerFieldValues: DeveloperFieldValue[] = [
    ...((session.dragFactor ?? 0) > 0 && Math.round(session.dragFactor) < 65535 ? [{ developer_data_index: 0, field_num: 2, value: Math.round(session.dragFactor) }] : []),
    // RecordingStrategy: StrokeBoundary
    { developer_data_index: 0, field_num: 10, value: 1 }
  ]

  fitWriter.writeMessage(
    'session',
    {
      timestamp: fitWriter.time(new Date(session.endTime as number)),
      message_index: 0,
      sport: 'rowing',
      sub_sport: 'indoorRowing',
      event: 'session',
      event_type: 'stop',
      trigger: 'activityEnd',
      sport_profile_name: 'Row Indoor',
      start_time: fitWriter.time(new Date(session.startTime)),
      ...(session.totalTime != undefined && session.totalTime >= 0 && session.totalTime < 4294967295 ? { total_elapsed_time: session.totalTime / 1000 } : {}),
      ...(session.totalTime != undefined && session.totalTime >= 0 && session.totalTime < 4294967295 ? { total_timer_time: session.totalTime / 1000 } : {}),
      ...(session.totalMovingTime != undefined && session.totalMovingTime >= 0 && session.totalMovingTime < 4294967295 ? { total_moving_time: session.totalMovingTime / 1000 } : {}),
      ...(session.totalLinearDistance != undefined && session.totalLinearDistance * 100 < 4294967295 ? { total_distance: session.totalLinearDistance } : {}),
      ...(session.totalWork != undefined && session.totalWork < 4294967295 ? { total_work: session.totalWork } : {}),
      ...(session.totalCalories != undefined && session.totalCalories < 65535 ? { total_calories: session.totalCalories } : {}),
      ...(session.strokeCount != undefined && session.strokeCount < 4294967295 ? { total_cycles: session.strokeCount } : {}),
      ...(session.averageLinearVelocity != undefined && session.averageLinearVelocity >= 0 && session.averageLinearVelocity <= 8.5 ? { avg_speed: session.averageLinearVelocity } : {}),
      ...(session.maximumLinearVelocity != undefined && session.maximumLinearVelocity >= 0 && session.maximumLinearVelocity <= 8.5 ? { max_speed: session.maximumLinearVelocity } : {}),
      ...(session.averagePower != undefined && session.averagePower >= 0 && session.averagePower <= 1650 ? { avg_power: session.averagePower } : {}),
      ...(session.maximumPower != undefined && session.maximumPower >= 0 && session.maximumPower <= 1650 ? { max_power: session.maximumPower } : {}),
      ...(session.averageHandleAvgForce != undefined && session.averageHandleAvgForce >= 0 && session.averageHandleAvgForce <= 2000 ? { avg_force: session.averageHandleAvgForce } : {}),
      ...(session.maximumHandleAvgForce != undefined && session.maximumHandleAvgForce >= 0 && session.maximumHandleAvgForce <= 2000 ? { max_force: session.maximumHandleAvgForce } : {}),
      ...((session?.averageStrokerate ?? 0) >= 10 && session?.averageStrokerate <= 200 ? { avg_cadence: session.averageStrokerate } : {}),
      ...((session?.maximumStrokerate ?? 0) >= 10 && session?.maximumStrokerate <= 200 ? { max_cadence: session.maximumStrokerate } : {}),
      ...((session?.minimumHeartrate ?? 0) > 0 && session.minimumHeartrate < 250 ? { min_heart_rate: session.minimumHeartrate } : {}),
      ...((session?.averageHeartrate ?? 0) > 0 && session.averageHeartrate < 250 ? { avg_heart_rate: session.averageHeartrate } : {}),
      ...((session?.maximumHeartrate ?? 0) > 0 && session.maximumHeartrate < 250 ? { max_heart_rate: session.maximumHeartrate } : {}),
      ...(session.averageStrokeDistance != undefined && session.averageStrokeDistance * 100 < 65535 ? { avg_stroke_distance: session.averageStrokeDistance } : {}),
      first_lap_index: 0,
      num_laps: splits.length
    },
    developerFieldValues,
    true
  )

  // Write the splits
  await writeSplits(fitWriter, workout)

  // Write the laps
  await writeLaps(fitWriter, workout)

  // Write the events
  await writeEvents(fitWriter, workout)

  await writeRecords(fitWriter, workout, maxForceCurvePointCount)

  return fitWriter.finish()
}

/**
 * Creation of all Garmin fit-splits (= rowing intervals). The split summaries classify
 * the HR of the strokes into active and rest by replaying the rest-split windows.
 * As no strokes occur during a rest, the rest HR can only come from the boundary
 * markers at the start and end of that rest.
 */
async function writeSplits (writer: any, workout: WorkoutData): Promise<void> {
  const { session, intervals, splits } = workout
  const activeIntervals = intervals.filter(i => i.intensity === 'active')
  const restIntervals = intervals.filter(i => i.intensity !== 'active')

  // The heartrate summaries are derived from the splits: the average heartrate of a split is weighted with the recorded length of that split,
  // so the sum of (average heartrate x time) divided by the total time of the splits that have a heartrate is the average heartrate
  let activeHeartrateTimeSum = 0
  let activeTimeWithHeartrate = 0
  let activeMaximumHeartrate = 0
  let restHeartrateTimeSum = 0
  let restTimeWithHeartrate = 0
  let restMaximumHeartrate = 0
  for (const split of splits) {
    const hasAverageHeartrate = (split.averageHeartrate ?? 0) > 0 && (split.totalTime ?? 0) > 0
    const hasMaximumHeartrate = (split.maximumHeartrate ?? 0) > 0
    if (split.intensity === 'active') {
      if (hasAverageHeartrate) { activeHeartrateTimeSum += split.averageHeartrate * split.totalTime; activeTimeWithHeartrate += split.totalTime }
      if (hasMaximumHeartrate) { activeMaximumHeartrate = Math.max(activeMaximumHeartrate, split.maximumHeartrate) }
    } else {
      if (hasAverageHeartrate) { restHeartrateTimeSum += split.averageHeartrate * split.totalTime; restTimeWithHeartrate += split.totalTime }
      if (hasMaximumHeartrate) { restMaximumHeartrate = Math.max(restMaximumHeartrate, split.maximumHeartrate) }
    }
  }
  const activeAverageHeartrate = activeTimeWithHeartrate > 0 ? activeHeartrateTimeSum / activeTimeWithHeartrate : 0
  const restAverageHeartrate = restTimeWithHeartrate > 0 ? restHeartrateTimeSum / restTimeWithHeartrate : 0
  // Write the split summary
  writer.writeMessage(
    'split_summary',
    {
      timestamp: writer.time(new Date(session.endTime as number)),
      message_index: 0,
      split_type: 'interval_active',
      num_splits: activeIntervals.length,
      ...(session.totalMovingTime != undefined && session.totalMovingTime >= 0 && session.totalMovingTime < 4294967295 ? { total_timer_time: session.totalMovingTime / 1000 } : {}),
      ...(session.totalLinearDistance != undefined && session.totalLinearDistance * 100 < 4294967295 ? { total_distance: session.totalLinearDistance } : {}),
      ...(session.averageLinearVelocity != undefined && session.averageLinearVelocity >= 0 && session.averageLinearVelocity <= 8.5 ? { avg_speed: session.averageLinearVelocity } : {}),
      ...(session.maximumLinearVelocity != undefined && session.maximumLinearVelocity >= 0 && session.maximumLinearVelocity <= 8.5 ? { max_speed: session.maximumLinearVelocity } : {}),
      ...((session.averageStrokerate ?? 0) >= 10 && session.averageStrokerate <= 200 ? { avg_cadence: session.averageStrokerate } : {}),
      ...((session.maximumStrokerate ?? 0) >= 10 && session.maximumStrokerate <= 200 ? { max_cadence: session.maximumStrokerate } : {}),
      ...(session.totalMovingCalories != undefined && session.totalMovingCalories < 4294967295 ? { total_calories: session.totalMovingCalories } : {}),
      ...(activeAverageHeartrate > 0 && activeAverageHeartrate < 255 ? { avg_heart_rate: activeAverageHeartrate } : {}),
      ...(activeMaximumHeartrate > 0 && activeMaximumHeartrate < 255 ? { max_heart_rate: activeMaximumHeartrate } : {})
    },
    null,
    restIntervals.length === 0
  )

  if (restIntervals.length > 0) {
    // There was a pause
    writer.writeMessage(
      'split_summary',
      {
        timestamp: writer.time(new Date(session.endTime as number)),
        message_index: 1,
        split_type: 'interval_rest',
        num_splits: restIntervals.length,
        ...(session.totalRestTime != undefined && session.totalRestTime >= 0 && session.totalRestTime < 4294967295 ? { total_timer_time: session.totalRestTime / 1000 } : {}),
        total_distance: 0,
        avg_speed: 0,
        max_speed: 0,
        avg_cadence: 0,
        max_cadence: 0,
        ...(session.totalRestCalories != undefined && session.totalRestCalories < 4294967295 ? { total_calories: session.totalRestCalories } : {}),
        ...(restAverageHeartrate > 0 && restAverageHeartrate < 255 ? { avg_heart_rate: restAverageHeartrate } : {}),
        ...(restMaximumHeartrate > 0 && restMaximumHeartrate < 255 ? { max_heart_rate: restMaximumHeartrate } : {})
      },
      null,
      true
    )
  }

  // Create the individual splits
  let i = 0
  while (i < intervals.length) {
    if (intervals[i].intensity === 'active') {
      await createActiveSplit(writer, workout, intervals[i])
    } else {
      // This is a rest interval
      await createRestSplit(writer, workout, intervals[i])
    }
    i++
  }
}

/**
 * Creation of the active fit-split (= Rowing interval)
 */
async function createActiveSplit (writer: any, workout: WorkoutData, interval: Interval): Promise<void> {
  if (interval.complete !== true) { return }
  const developerFieldValues: DeveloperFieldValue[] = [
    ...((interval.dragFactor ?? 0) > 0 && Math.round(interval.dragFactor) < 65535 ? [{ developer_data_index: 0, field_num: 2, value: Math.round(interval.dragFactor) }] : [])
  ]

  writer.writeMessage(
    'split',
    {
      timestamp: writer.time(new Date(workout.session.endTime as number)),
      message_index: interval.intervalNumber,
      ...(interval.firstSplitNumber != undefined && interval.firstSplitNumber < 65535 ? { lap_index: interval.firstSplitNumber } : {}),
      sport: 'rowing',
      sub_sport: 'indoorRowing',
      split_type: 'interval_active',
      ...(interval.totalTime != undefined && interval.totalTime >= 0 && interval.totalTime < 4294967295 ? { total_elapsed_time: interval.totalTime / 1000 } : {}),
      ...(interval.totalTime != undefined && interval.totalTime >= 0 && interval.totalTime < 4294967295 ? { total_timer_time: interval.totalTime / 1000 } : {}),
      ...(interval.totalMovingTime != undefined && interval.totalMovingTime >= 0 && interval.totalMovingTime < 4294967295 ? { total_moving_time: interval.totalMovingTime / 1000 } : {}),
      ...(interval.totalLinearDistance != undefined && interval.totalLinearDistance * 100 < 4294967295 ? { total_distance: interval.totalLinearDistance } : {}),
      ...(interval.averageLinearVelocity != undefined && interval.averageLinearVelocity >= 0 && interval.averageLinearVelocity <= 8.5 ? { avg_speed: interval.averageLinearVelocity } : {}),
      ...(interval.maximumLinearVelocity != undefined && interval.maximumLinearVelocity >= 0 && interval.maximumLinearVelocity <= 8.5 ? { max_speed: interval.maximumLinearVelocity } : {}),
      ...(interval.averagePower != undefined && interval.averagePower >= 0 && interval.averagePower <= 1650 ? { avg_power: interval.averagePower } : {}),
      ...(interval.maximumPower != undefined && interval.maximumPower >= 0 && interval.maximumPower <= 1650 ? { max_power: interval.maximumPower } : {}),
      ...((interval.averageStrokerate ?? 0) >= 10 && interval.averageStrokerate <= 200 ? { avg_cadence: interval.averageStrokerate } : {}),
      ...((interval.maximumStrokerate ?? 0) >= 10 && interval.maximumStrokerate <= 200 ? { max_cadence: interval.maximumStrokerate } : {}),
      ...(interval.calories != undefined && interval.calories < 4294967295 ? { total_calories: interval.calories } : {}),
      start_time: writer.time(new Date(interval.startTime)),
      ...(interval.startDistance != undefined && interval.startDistance * 100 < 4294967295 ? { start_distance: interval.startDistance } : {}),
      ...(interval.endTime != undefined ? { end_time: writer.time(new Date(interval.endTime)) } : {}),
      ...((interval.averageHeartrate ?? 0) > 0 && interval.averageHeartrate < 255 ? { avg_heart_rate: interval.averageHeartrate } : {}),
      ...((interval.maximumHeartrate ?? 0) > 0 && interval.maximumHeartrate < 255 ? { max_heart_rate: interval.maximumHeartrate } : {})
    },
    developerFieldValues,
    (interval.intervalNumber + 1) === workout.intervals.length
  )
}

/**
 * Creation of the rest fit-split (= A planned rowing rest interval)
 */
async function createRestSplit (writer: any, workout: WorkoutData, interval: Interval): Promise<void> {
  if (interval.complete !== true) { return }

  writer.writeMessage(
    'split',
    {
      timestamp: writer.time(new Date(workout.session.endTime as number)),
      message_index: interval.intervalNumber,
      ...(interval.firstSplitNumber != undefined && interval.firstSplitNumber < 65535 ? { lap_index: interval.firstSplitNumber } : {}),
      sport: 'rowing',
      sub_sport: 'indoorRowing',
      split_type: 'interval_rest',
      ...(interval.totalTime != undefined && interval.totalTime >= 0 && interval.totalTime < 4294967295 ? { total_elapsed_time: interval.totalTime / 1000 } : {}),
      ...(interval.totalTime != undefined && interval.totalTime >= 0 && interval.totalTime < 4294967295 ? { total_timer_time: interval.totalTime / 1000 } : {}),
      total_moving_time: 0,
      total_distance: 0,
      avg_speed: 0,
      max_speed: 0,
      avg_power: 0,
      max_power: 0,
      avg_cadence: 0,
      max_cadence: 0,
      ...(interval.calories != undefined && interval.calories < 4294967295 ? { total_calories: interval.calories } : {}),
      start_time: writer.time(new Date(interval.startTime)),
      ...(interval.startDistance != undefined && interval.startDistance * 100 < 4294967295 ? { start_distance: interval.startDistance } : {}),
      ...(interval.endTime != undefined ? { end_time: writer.time(new Date(interval.endTime)) } : {}),
      ...((interval.averageHeartrate ?? 0) > 0 && interval.averageHeartrate < 255 ? { avg_heart_rate: interval.averageHeartrate } : {}),
      ...((interval.maximumHeartrate ?? 0) > 0 && interval.maximumHeartrate < 255 ? { max_heart_rate: interval.maximumHeartrate } : {})
    },
    null,
    (interval.intervalNumber + 1) === workout.intervals.length
  )
}

async function writeLaps (writer: any, workout: WorkoutData): Promise<void> {
  // Write all laps
  let i = 0
  while (i < workout.splits.length) {
    if (workout.splits[i].intensity === 'active') {
      await createActiveLap(writer, workout, workout.splits[i])
    } else {
      // This is a rest split
      await createRestLap(writer, workout, workout.splits[i])
    }
    i++
  }
}

async function createActiveLap (writer: any, workout: WorkoutData, split: Split): Promise<void> {
  // It is an active lap, after we make sure it is a completed lap, we can write it
  if (split.complete !== true) { return }
  const developerFieldValues: DeveloperFieldValue[] = [
    ...((split.dragFactor ?? 0) > 0 && Math.round(split.dragFactor) < 65535 ? [{ developer_data_index: 0, field_num: 2, value: Math.round(split.dragFactor) }] : [])
  ]

  writer.writeMessage(
    'lap',
    {
      timestamp: writer.time(new Date(workout.session.endTime as number)),
      message_index: split.splitNumber,
      sport: 'rowing',
      sub_sport: 'indoorRowing',
      event: split.fitEvent ?? 'lap',
      event_type: split.fitEventType ?? 'stop',
      intensity: 'active',
      ...(workout.splits.length === (split.splitNumber + 1) ? { lap_trigger: 'sessionEnd' } : { lap_trigger: split.fitLapTrigger ?? 'manual' }),
      start_time: writer.time(new Date(split.startTime)),
      ...(split.totalTime != undefined && split.totalTime >= 0 && split.totalTime < 4294967295 ? { total_elapsed_time: split.totalTime / 1000 } : {}),
      ...(split.totalTime != undefined && split.totalTime >= 0 && split.totalTime < 4294967295 ? { total_timer_time: split.totalTime / 1000 } : {}),
      ...(split.totalMovingTime != undefined && split.totalMovingTime >= 0 && split.totalMovingTime < 4294967295 ? { total_moving_time: split.totalMovingTime / 1000 } : {}),
      ...(split.totalLinearDistance != undefined && split.totalLinearDistance * 100 < 4294967295 ? { total_distance: split.totalLinearDistance } : {}),
      ...(split.strokeCount != undefined && split.strokeCount < 4294967295 ? { total_cycles: split.strokeCount } : {}),
      ...((split.averageStrokerate ?? 0) >= 10 && split.averageStrokerate <= 200 ? { avg_cadence: split.averageStrokerate } : {}),
      ...((split.maximumStrokerate ?? 0) >= 10 && split.maximumStrokerate <= 200 ? { max_cadence: split.maximumStrokerate } : {}),
      ...(split.averageStrokeDistance != undefined && split.averageStrokeDistance * 100 < 65535 ? { avg_stroke_distance: split.averageStrokeDistance } : {}),
      ...(split.workDone != undefined && split.workDone < 4294967295 ? { total_work: split.workDone } : {}),
      ...(split.calories != undefined && split.calories < 65535 ? { total_calories: split.calories } : {}),
      ...(split.averageLinearVelocity != undefined && split.averageLinearVelocity >= 0 && split.averageLinearVelocity <= 8.5 ? { avg_speed: split.averageLinearVelocity } : {}),
      ...(split.maximumLinearVelocity != undefined && split.maximumLinearVelocity >= 0 && split.maximumLinearVelocity <= 8.5 ? { max_speed: split.maximumLinearVelocity } : {}),
      ...(split.averagePower != undefined && split.averagePower >= 0 && split.averagePower <= 1650 ? { avg_power: split.averagePower } : {}),
      ...(split.maximumPower != undefined && split.maximumPower >= 0 && split.maximumPower <= 1650 ? { max_power: split.maximumPower } : {}),
      ...(split.averageHandleAvgForce != undefined && split.averageHandleAvgForce >= 0 && split.averageHandleAvgForce <= 2000 ? { avg_force: split.averageHandleAvgForce } : {}),
      ...(split.maximumHandleAvgForce != undefined && split.maximumHandleAvgForce >= 0 && split.maximumHandleAvgForce <= 2000 ? { max_force: split.maximumHandleAvgForce } : {}),
      ...((split.minimumHeartrate ?? 0) > 0 && split.minimumHeartrate < 255 ? { min_heart_rate: split.minimumHeartrate } : {}),
      ...((split.averageHeartrate ?? 0) > 0 && split.averageHeartrate < 255 ? { avg_heart_rate: split.averageHeartrate } : {}),
      ...((split.maximumHeartrate ?? 0) > 0 && split.maximumHeartrate < 255 ? { max_heart_rate: split.maximumHeartrate } : {})
    },
    developerFieldValues,
    workout.splits.length === (split.splitNumber + 1)
  )
}

async function createRestLap (writer: any, workout: WorkoutData, split: Split): Promise<void> {
  // First, make sure the rest lap has ended
  if (split.endTime === null) { return }

  writer.writeMessage(
    'lap',
    {
      timestamp: writer.time(new Date(workout.session.endTime as number)),
      message_index: split.splitNumber,
      sport: 'rowing',
      sub_sport: 'indoorRowing',
      event: split.fitEvent ?? 'lap',
      event_type: split.fitEventType ?? 'stop',
      intensity: 'rest',
      lap_trigger: split.fitLapTrigger ?? 'manual',
      start_time: writer.time(new Date(split.startTime)),
      ...(split.totalTime != undefined && split.totalTime >= 0 && split.totalTime < 4294967295 ? { total_elapsed_time: split.totalTime / 1000 } : {}),
      ...(split.totalTime != undefined && split.totalTime >= 0 && split.totalTime < 4294967295 ? { total_timer_time: split.totalTime / 1000 } : {}),
      total_moving_time: 0,
      total_distance: 0,
      total_cycles: 0,
      avg_cadence: 0,
      max_cadence: 0,
      avg_stroke_distance: 0,
      ...(split.calories != undefined && split.calories < 65535 ? { total_calories: split.calories } : {}),
      avg_speed: 0,
      max_speed: 0,
      avg_power: 0,
      max_power: 0,
      ...((split.minimumHeartrate ?? 0) > 0 && split.minimumHeartrate < 255 ? { min_heart_rate: split.minimumHeartrate } : {}),
      ...((split.averageHeartrate ?? 0) > 0 && split.averageHeartrate < 255 ? { avg_heart_rate: split.averageHeartrate } : {}),
      ...((split.maximumHeartrate ?? 0) > 0 && split.maximumHeartrate < 255 ? { max_heart_rate: split.maximumHeartrate } : {})
    },
    null,
    workout.splits.length === (split.splitNumber + 1)
  )
}

/**
 * Write all events to the FIT-file. The recorder does not store a timer-event
 * timeline; it is deduced here by replaying the rest splits: each rest split
 * stops the timer at its start and restarts it at its end.
 */
async function writeEvents (writer: any, workout: WorkoutData): Promise<void> {
  // Start of the session
  await addEvent(writer, new Date(workout.session.startTime), 'timer', 'start')

  // Write all pauses
  let i = 0
  while (i < workout.splits.length) {
    const split = workout.splits[i]
    if (split.intensity !== 'active' && split.endTime !== null) {
      // This is a rest split
      await addEvent(writer, new Date(split.startTime), split.fitEvent ?? 'lap', 'stop')
      await addEvent(writer, new Date(split.endTime as number), 'timer', 'start')
    }
    i++
  }

  // Finish the session with a stop event
  await addEvent(writer, new Date(workout.session.endTime as number), 'timer', 'stopAll')
}

async function addEvent (writer: any, time: Date, event: string, eventType: string): Promise<void> {
  writer.writeMessage(
    'event',
    {
      timestamp: writer.time(time),
      event: event,
      event_type: eventType,
      event_group: 0
    },
    null,
    true
  )
}

/**
 * @description This loops through all recorded strokes (including the boundary
 * markers, which anchor the laps and splits) and adds them to the fit-structure
 */
async function writeRecords (writer: any, workout: WorkoutData, maxForceCurvePointCount: number): Promise<void> {
  const { session, strokes, splits } = workout
  // The windows of the rest splits, which determine the WorkoutState of a record. The windows are
  // half-open: the end of a rest split is the start of the next split, and belongs to that one
  const restWindows = splits
    .filter(s => s.intensity !== 'active' && s.endTime !== null)
    .map(s => ({ start: s.startTime, end: s.endTime as number }))
  if ((session.totalMovingTime ?? 0) > 0 && strokes.length > 0 && (strokes[strokes.length - 1].totalLinearDistance ?? 0) > 0) {
    let i = 0
    while (i < strokes.length) {
      await createTrackPoint(writer, strokes[i], restWindows, maxForceCurvePointCount)
      i++
    }
  }
}

/**
 * @description This creates the individual stroke. As the FitWriter does not apply the
 * declared scale to developer fields, every developer value is scaled here.
 * Some consumers require boundary markers, to mark the start and end of a session and rest periods.
 * @see {@link https://github.com/MoveLab-Studio/rowing-data-standard/blob/main/spec/FIT_STANDARD.md|the harmonised rowing data FIT specifications for definitions and more information}
 */
async function createTrackPoint (writer: any, stroke: Stroke, restWindows: { start: number; end: number }[], maxForceCurvePointCount: number): Promise<void> {
  // WorkoutState uses the values of the native FIT intensity enum: 0 = active, 1 = rest
  const workoutState = restWindows.some(w => stroke.timestamp >= w.start && stroke.timestamp < w.end) ? 1 : 0

  // A boundary marker has a valid pace and power, unless it is at the end of a pause, as the flywheel was standing still
  // then. Only for those markers pace and power are reported as 0. The marker at the start of a pause is a normal one
  const isPauseEnd = stroke.boundaryMarker && restWindows.some(w => stroke.timestamp > w.start && stroke.timestamp <= w.end)
  const speed = isPauseEnd ? 0 : stroke.linearVelocity
  const power = isPauseEnd ? 0 : stroke.power

  // The peak force dependent values are only written when there is a force curve to report
  const hasPeakDriveForce = maxForceCurvePointCount > 0 && (stroke.peakDriveForce ?? 0) > 0 && stroke.peakDriveForce <= 2000
  // The absolute handle position (mm) at peak force is the normalised position (0-1) along the drive length
  const peakForcePositionAbs = Math.round((stroke.peakDriveForcePosition ?? 0) * (stroke.driveLength ?? 0))

  // The handle positions are derived from the drive length, so they are only reported when the drive length is plausible (100-2100 mm)
  const hasDriveLength = (stroke.driveLength ?? 0) >= 100 && stroke.driveLength <= 2100

  // The absolute handle position (mm) at peak force is the normalised position (0-1) of the peak force along the drive length
  const peakForcePositionAbs = stroke.peakDriveForcePosition != undefined && hasDriveLength ? Math.round(stroke.peakDriveForcePosition * stroke.driveLength) : undefined
  // The force curve is sampled uniformly along the handle distance (abscissa type 2). The sample interval is the
  // spacing of the samples over the full curve, so it stays correct when the curve has to be cut to the declared size
  const forceCurve = stroke.forceCurve ?? []
  const forceCurvePointCount = Math.min(forceCurve.length, maxForceCurvePointCount)
  const sampleInterval = forceCurve.length > 1 && hasDriveLength ? Math.round(stroke.driveLength / (forceCurve.length - 1)) : undefined
  // Negative forces are written as 0 (as the standard requires). A curve with a sample above 2000 N is not plausible and is left out entirely
  const forceCurveIsPlausible = forceCurve.slice(0, forceCurvePointCount).every(force => !(Number(force) > 2000))
  const forceCurveSamples = Array.from({ length: maxForceCurvePointCount }, (_, i) => {
    const force = i < forceCurvePointCount ? Number(forceCurve[i]) : 0
    return Number.isFinite(force) ? Math.max(0, Math.round(force * 10)) : 0
  })

  const developerFieldValues: DeveloperFieldValue[] = [
    { developer_data_index: 0, field_num: 9, value: workoutState },
    ...((stroke.strokeWork ?? 0) > 0 && Math.round(stroke.strokeWork) < 65535 ? [{ developer_data_index: 0, field_num: 19, value: Math.round(stroke.strokeWork) }] : []),
    ...((stroke.dragFactor ?? 0) > 0 && Math.round(stroke.dragFactor) < 65535 ? [{ developer_data_index: 0, field_num: 2, value: Math.round(stroke.dragFactor) }] : []),
    ...((stroke.driveDuration ?? 0) > 0 && Math.round(stroke.driveDuration) < 65535 ? [{ developer_data_index: 0, field_num: 1, value: Math.round(stroke.driveDuration) }] : []),
    ...((stroke.recoveryDuration ?? 0) > 0 && Math.round(stroke.recoveryDuration) < 65535 ? [{ developer_data_index: 0, field_num: 3, value: Math.round(stroke.recoveryDuration) }] : []),
    ...(hasDriveLength ? [{ developer_data_index: 0, field_num: 0, value: Math.round(stroke.driveLength) }] : []),
    ...((stroke.linearVelocity ?? 0) > 0 && stroke.linearVelocity <= 8.5 ? [{ developer_data_index: 0, field_num: 8, value: Math.round(stroke.linearVelocity * 100) }] : []),
    ...(maxForceCurvePointCount > 0 && (stroke.averageDriveForce ?? 0) > 0 && stroke.averageDriveForce <= 2000 ? [{ developer_data_index: 0, field_num: 6, value: Math.round(stroke.averageDriveForce * 10) }] : []),
    ...(hasPeakDriveForce ? [{ developer_data_index: 0, field_num: 7, value: Math.round(stroke.peakDriveForce * 10) }] : []),
    ...(hasPeakDriveForce && (stroke.peakDriveForcePosition ?? -1) >= 0 && Math.round(stroke.peakDriveForcePosition * 100) < 65535 ? [{ developer_data_index: 0, field_num: 17, value: Math.round(stroke.peakDriveForcePosition * 100) }] : []),
    ...(hasPeakDriveForce && peakForcePositionAbs != undefined && peakForcePositionAbs >= 0 && peakForcePositionAbs < 65535 ? [{ developer_data_index: 0, field_num: 18, value: peakForcePositionAbs }] : []),
    ...(forceCurvePointCount > 1 && forceCurveIsPlausible && (sampleInterval ?? 0) > 0 && (sampleInterval as number) < 65535
      ? [
          { developer_data_index: 0, field_num: 90, value: 2 },
          { developer_data_index: 0, field_num: 91, value: sampleInterval as number },
          { developer_data_index: 0, field_num: 92, value: forceCurvePointCount },
          { developer_data_index: 0, field_num: 60, value: forceCurveSamples }
        ]
      : [])
  ]

  writer.writeMessage(
    'record',
    {
      timestamp: writer.time(new Date(stroke.timestamp)),
      ...(stroke.totalLinearDistance != undefined && stroke.totalLinearDistance * 100 < 4294967295 ? { distance: stroke.totalLinearDistance } : {}),
      ...(stroke.totalWork != undefined && stroke.totalWork < 4294967295 ? { accumulated_power: stroke.totalWork } : {}),
      ...(stroke.totalCalories != undefined && stroke.totalCalories < 65535 ? { calories: stroke.totalCalories } : {}),
      ...(stroke.strokeNumber != undefined && stroke.strokeNumber < 4294967295 ? { total_cycles: stroke.strokeNumber } : {}),
      activity_type: 'fitnessEquipment',
      ...(((speed ?? 0) > 0 || (stroke.boundaryMarker && (speed ?? -1) >= 0)) && speed <= 8.5 ? { speed: speed } : {}),
      ...(((power ?? 0) > 0 || (stroke.boundaryMarker && (power ?? -1) >= 0)) && power <= 1650 ? { power: power } : {}),
      ...((stroke.strokeRate ?? 0) >= 10 && stroke.strokeRate <= 200 ? { cadence: Math.round(stroke.strokeRate as number) } : {}),
      ...((stroke.strokeRate ?? 0) >= 10 && stroke.strokeRate <= 200 ? { cadence256: stroke.strokeRate } : {}),
      ...((stroke.strokeDistance ?? 0) > 0 && stroke.strokeDistance * 100 < 65535 ? { cycle_length16: stroke.strokeDistance } : {}),
      ...((stroke.dragFactor ?? 0) > 0 && (stroke.dragFactor as number) < 255 ? { resistance: stroke.dragFactor } : {}), // As the data is stored in an int8, we need to guard against exceeding that
      ...((stroke.heartrate ?? 0) > 0 && stroke.heartrate < 255 ? { heart_rate: stroke.heartrate } : {}),
      ...(stroke.averageDriveForce != undefined && stroke.averageDriveForce >= 0 && stroke.averageDriveForce <= 2000 ? { force: stroke.averageDriveForce } : {})
    },
    developerFieldValues
  )
}
